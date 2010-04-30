from zope.interface import implements

import txamqp.spec
from txamqp.content import Content
from txamqp.protocol import AMQClient
from txamqp.client import TwistedDelegate
from txamqp.queue import Empty

from twisted.python import usage, log
from twisted.internet import error, protocol, reactor
from twisted.internet.defer import inlineCallbacks, Deferred, returnValue
from twisted.application.service import IServiceMaker
from twisted.application import internet
from twisted.plugin import IPlugin
import json

class Options(usage.Options):
    optParameters = [
        ["ssmi-username", None, None, "SSMI username"],
        ["ssmi-password", None, None, "SSMI password"],
        ["ssmi-host", None, None, "SSMI host"],
        ["ssmi-port", None, None, "SSMI host's port", int],
        ["amqp-host", None, "localhost", "AMQP host"],
        ["amqp-port", None, 5672, "AMQP port", int],
        ["amqp-username", None, "richmond", "AMQP username"],
        ["amqp-password", None, "richmond", "AMQP password"],
        ["amqp-vhost", None, "/richmond", "AMQP virtual host"],
        ["amqp-queue", None, "richmond", "AMQP queue"],
        ["amqp-exchange", None, "richmond", "AMQP exchange"],
        ["amqp-receive-routing-key", None, "ssmi.receive", "AMQP routing key"],
        ["amqp-send-routing-key", None, "ssmi.send", "AMQP routing key"],
    ]


class Starter(object):
    
    def __init__(self, username, password, queue_name, exchange_name):
        self.username = username
        self.password = password
        self.queue_name = queue_name
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
        yield channel.queue_declare(queue=self.queue_name)
        log.msg("Connected to queue richmond")
        yield channel.exchange_declare(exchange=self.exchange_name, type="direct")
        log.msg("Connected to exchange richmond")
        yield channel.queue_bind(queue=self.queue_name, 
                                    exchange=self.exchange_name, 
                                    routing_key="ssmi.receive")
        log.msg("Bound queue to exchange")
        returnValue(channel)
    
    @inlineCallbacks
    def create_consumer(self, channel):
        reply = yield channel.basic_consume(queue=self.queue_name)
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
            print 'Received: ' + msg.content.body + ' from channel #' + str(channel.id)
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
        
        queue.setChannel(channel)
        ssmi_service = SSMIService(ssmi_username, ssmi_password, queue)
        
        def app_register(ssmi_protocol):
            return ssmi_service.register_ssmi(ssmi_protocol)
        
        yield reactor.connectTCP(ssmi_host, ssmi_port, 
                            SSMIFactory(app_register_callback=app_register))
        


class DumbQueue(object):
    def __init__(self, exchange_name, routing_key):
        self.exchange_name = exchange_name
        self.routing_key = routing_key
    
    def setChannel(self, channel):
        self.channel = channel
    
    def send(self, data):
        self.channel.basic_publish(exchange=self.exchange_name, 
                                    content=Content(json.dumps(data)), 
                                    routing_key=self.routing_key)


class AMQPServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "broker"
    description = "Connect to AMQP broker"
    options = Options
    
    def makeService(self, options):
        delegate = TwistedDelegate()
        onConn = Deferred()
        
        host = options['amqp-host']
        port = options['amqp-port']
        user = options['amqp-username']
        password = options['amqp-password']
        vhost = options['amqp-vhost']
        spec = 'amqp-spec-0-8.xml'  # for some reason txAMQP wants to load the 
                                    # spec each time it starts
        
        ssmi_host = options['ssmi-host']
        ssmi_port = options['ssmi-port']
        ssmi_username = options['ssmi-username']
        ssmi_password = options['ssmi-password']
        
        
        starter = Starter(
            username = options['amqp-username'],
            password = options['amqp-password'],
            queue_name = options['amqp-queue'],
            exchange_name = options['amqp-exchange']
        )
        
        delegate = TwistedDelegate()
        onConnect = Deferred()
        onConnect.addCallback(starter.got_connection)
        onConnect.addCallback(starter.is_authenticated)
        onConnect.addCallback(starter.create_consumer)
        onConnect.addCallback(starter.create_publisher)
        queue = DumbQueue(options['amqp-exchange'], 
                            options['amqp-receive-routing-key'])
        onConnect.addCallback(starter.start_ssmi_client, ssmi_host, ssmi_port, ssmi_username, ssmi_password, queue)
        
        def failed_connection(thefailure):
            thefailure.trap(error.ConnectionRefusedError)
            print "failed to connect to host: %s, port: %s, failure: %r" % (host, port, thefailure,)
            thefailure.raiseException()
        onConnect.addErrback(failed_connection)
        
        prot = AMQClient(delegate, vhost, txamqp.spec.load(spec))
        factory = protocol._InstanceFactory(reactor, prot, onConnect)

        return internet.TCPClient(host, port, factory)


serviceMaker = AMQPServiceMaker()