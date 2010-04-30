from zope.interface import implements

import txamqp.spec
from txamqp.content import Content
from txamqp.protocol import AMQClient
from txamqp.client import TwistedDelegate
from txamqp.queue import Empty

from twisted.python import usage, log
from twisted.internet import error, protocol, reactor
from twisted.internet.defer import inlineCallbacks, Deferred, returnValue
from twisted.application.service import IServiceMaker, MultiService
from twisted.application import internet
from twisted.plugin import IPlugin
import json

from richmond.utils import filter_options_on_prefix

class Options(usage.Options):
    optParameters = [
        ["config", "c", None, "Read options from config file"],
        ["ssmi-username", None, None, "SSMI username"],
        ["ssmi-password", None, None, "SSMI password"],
        ["ssmi-host", None, None, "SSMI host"],
        ["ssmi-port", None, None, "SSMI host's port", int],
        ["amqp-host", None, "localhost", "AMQP host"],
        ["amqp-port", None, 5672, "AMQP port", int],
        ["amqp-username", None, "richmond", "AMQP username"],
        ["amqp-password", None, "richmond", "AMQP password"],
        ["amqp-spec", None, "config/amqp-spec-0-8.xml", "AMQP spec file"],
        ["amqp-vhost", None, "/richmond", "AMQP virtual host"],
        ["amqp-send-queue", None, "richmond.send", "AMQP send queue"],
        ["amqp-send-routing-key", None, "ssmi.send", "AMQP routing key"],
        ["amqp-exchange", None, "richmond", "AMQP exchange"],
        ["amqp-receive-queue", None, "richmond.receive", "AMQP receive queue"],
        ["amqp-receive-routing-key", None, "ssmi.receive", "AMQP routing key"],
    ]
    
    def opt_config(self, path):
        """
        Read the options from a config file rather than command line, uses
        the ConfigParser from stdlib. Section headers are prepended to the
        options and together make up the command line parameter:
        
            [amqp]
            host: localhost
            port: 5672
        
        Equals to
        
            twistd ... --amqp-host=localhost --amqp-port=5672
        
        """
        import ConfigParser
        config = ConfigParser.ConfigParser()
        config.readfp(open(path))
        for section in config.sections():
            for option in config.options(section):
                parameter_name = '%s-%s' % (section, option)
                # don't need to do getint / getfloat etc... here, Twisted's
                # usage.Options does the validation / coerce stuff for us
                parameter_value = config.get(section, option)
                dispatcher = self._dispatch[parameter_name]
                dispatcher.dispatch(parameter_name, parameter_value)
    opt_c = opt_config


class Starter(object):
    def __init__(self, username, password, send_queue_name, receive_queue_name, exchange_name):
        self.username = username
        self.password = password
        self.send_queue_name = send_queue_name
        self.receive_queue_name = receive_queue_name
        self.exchange_name = exchange_name
        self.connection = None
        self.channel = None
    
    @inlineCallbacks
    def got_connection(self, connection):
        log.msg("Connected to the broker, authenticating ...")
        yield connection.authenticate(self.username, self.password)
        returnValue(connection)
    
    @inlineCallbacks
    def is_authenticated(self, connection):
        self.connection = connection
        log.msg("Authenticated. Opening queue & channels")
        channel = yield connection.channel(1)
        self.channel = channel
        yield channel.channel_open()
        log.msg("Channel opened")
        yield channel.queue_declare(queue=self.send_queue_name)
        log.msg("Connected to receive queue %s" % self.send_queue_name)
        yield channel.queue_declare(queue=self.receive_queue_name)
        log.msg("Connected to receive queue %s" % self.receive_queue_name)
        yield channel.exchange_declare(exchange=self.exchange_name, type="direct")
        log.msg("Connected to exchange richmond")
        yield channel.queue_bind(queue=self.send_queue_name, 
                                    exchange=self.exchange_name, 
                                    routing_key="ssmi.send")
        log.msg("Bound %s to exchange with routing_key ssmi.send" % self.send_queue_name)
        yield channel.queue_bind(queue=self.receive_queue_name, 
                                    exchange=self.exchange_name, 
                                    routing_key="ssmi.receive")
        log.msg("Bound %s to exchange with routing_key ssmi.reveive" % self.receive_queue_name)
        returnValue(channel)
    
    @inlineCallbacks
    def create_consumer(self, channel):
        reply = yield channel.basic_consume(queue=self.send_queue_name)
        log.msg("Registered the consumer")
        queue = yield self.connection.queue(reply.consumer_tag)
        log.msg("Got a queue: %s" % queue)
        
        deferred_consumer = self.start_consumer(channel, queue)
        returnValue(channel)
    
    @inlineCallbacks
    def start_consumer(self, channel, queue):
        while True:
            log.msg("Waiting for messages")
            msg = yield queue.get()
            data = json.loads(msg.content.body)
            print 'received data', data, 'on', self.receive_queue_name, 'routing_key ssmi.send'
            if hasattr(self.ssmi_service, 'ssmi_client'):
                self.ssmi_service.send_ussd(str(data['msisdn']), str(data['message']), str(data['ussd_type']))
            channel.basic_ack(msg.delivery_tag, True)
        returnValue(channel)
    
    @inlineCallbacks
    def create_publisher(self, channel):
        log.msg("channel: %s " % channel)
        log.msg("creating publisher")
        yield channel
        returnValue(channel)
    
    @inlineCallbacks
    def start_ssmi_client(self, channel, ssmi_host, ssmi_port, ssmi_username, 
                            ssmi_password, queue):
        from amqp import SSMIService, SSMIFactory
        
        self.ssmi_service = SSMIService(ssmi_username, ssmi_password, queue)
        
        def app_register(ssmi_protocol):
            return self.ssmi_service.register_ssmi(ssmi_protocol)
        
        yield reactor.connectTCP(ssmi_host, ssmi_port, 
                            SSMIFactory(app_register_callback=app_register))
        returnValue(channel)
    
    @inlineCallbacks
    def attach_channel(self, channel):
        self.ssmi_service.setChannel(channel)
        yield channel
        returnValue(channel)


class DumbQueue(object):
    def __init__(self, exchange_name, routing_key):
        self.exchange_name = exchange_name
        self.routing_key = routing_key
    
    def setChannel(self, channel):
        self.channel = channel
    
    def send(self, data):
        str_data = json.dumps(data)
        log.msg("publishing %s to exchange %s with routing key %s" % 
                    (str_data, self.exchange_name, self.routing_key))
        self.channel.basic_publish(exchange=self.exchange_name, 
                                    content=Content(str_data), 
                                    routing_key=self.routing_key)


class AMQPServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "richmond"
    description = "Connect to SSMI to AMQP broker"
    options = Options
    
    def amqp_options(self, options):
        return filter_options_on_prefix(options, "amqp")
    
    def ssmi_options(self, options):
        return filter_options_on_prefix(options, "ssmi")
    
    def makeService(self, options):
        delegate = TwistedDelegate()
        onConn = Deferred()
        
        amqp_options = self.amqp_options(options)
        ssmi_options = self.ssmi_options(options)
        
        host = amqp_options['host']
        port = amqp_options['port']
        user = amqp_options['username']
        password = amqp_options['password']
        vhost = amqp_options['vhost']
        spec = amqp_options['spec']  # for some reason txAMQP wants to load the 
                                    # spec each time it starts
        
        ssmi_host = ssmi_options['host']
        ssmi_port = ssmi_options['port']
        ssmi_username = ssmi_options['username']
        ssmi_password = ssmi_options['password']
                
        
        starter = Starter(
            username = options['amqp-username'],
            password = options['amqp-password'],
            send_queue_name = options['amqp-send-queue'],
            receive_queue_name = options['amqp-receive-queue'],
            exchange_name = options['amqp-exchange']
        )
        
        queue = DumbQueue(options['amqp-exchange'], 
                            options['amqp-receive-routing-key'])
        delegate = TwistedDelegate()
        onConnect = Deferred()
        onConnect.addCallback(starter.got_connection)
        onConnect.addCallback(starter.is_authenticated)
        onConnect.addCallback(starter.start_ssmi_client, ssmi_host, ssmi_port, ssmi_username, ssmi_password, queue)
        onConnect.addCallback(starter.create_consumer)
        onConnect.addCallback(starter.create_publisher)
        onConnect.addCallback(starter.attach_channel)
        
        def failed_connection(thefailure):
            thefailure.trap(error.ConnectionRefusedError)
            print "failed to connect to host: %s, port: %s, failure: %r" % (host, port, thefailure,)
            thefailure.raiseException()
        onConnect.addErrback(failed_connection)
        
        prot = AMQClient(delegate, vhost, txamqp.spec.load(spec))
        factory = protocol._InstanceFactory(reactor, prot, onConnect)

        # return internet.TCPClient(host, port, factory)
       
        from richmond.service.amqp_service import AMQPService
        from richmond.service.ssmi_service import SSMIService
         
        multi_service = MultiService()
        multi_service.addService(SSMIService(ssmi_username, ssmi_password,
                                                ssmi_host, ssmi_port))
        multi_service.addService(AMQPService())
        return multi_service

serviceMaker = AMQPServiceMaker()
