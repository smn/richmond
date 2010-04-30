from zope.interface import implements
from getpass import getpass

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application import internet
from twisted.application.service import IServiceMaker
# from twisted.internet.protocol import ClientCreator
from twisted.internet import reactor, task, defer

from carrot.connection import BrokerConnection
from carrot.messaging import Consumer, Publisher


# from txamqp.protocol import AMQClient
# from txamqp.client import TwistedDelegate
# from txamqp.content import Content

from ssmi.client import SSMIFactory
from ssmi.client import (SSMI_USSD_TYPE_NEW, SSMI_USSD_TYPE_EXISTING, 
                            SSMI_USSD_TYPE_END, SSMI_USSD_TYPE_TIMEOUT)
import logging



class SSMIService(object):
    """A Service which can be hooked into a Twisted reactor loop"""
    def __init__(self, username, password, queue):
        self.username = username
        self.password = password
        self.queue = queue
    
    def register_ssmi(self, ssmi_protocol):
        self.ssmi_client = ssmi_protocol
        self.ssmi_client.app_setup(username=self.username, 
                                    password=self.password,
                                    ussd_callback=self.process_ussd, 
                                    sms_callback=self.process_sms)
    
    def send_ussd(self, msisdn, text, reply_type):
        return self.ssmi_client.send_ussd(msisdn, text, reply_type)
    
    def process_sms(self, *args, **kwargs):
        raise NotImplementedError, "process_sms not implemented"
    
    def process_ussd(self, msisdn, ussd_type, ussd_phase, message):
        if self.ssmi_client is None:
            log.err('FATAL: client not registered')
            return
        
        routes = [
            SSMI_USSD_TYPE_NEW,
            SSMI_USSD_TYPE_EXISTING,
            SSMI_USSD_TYPE_TIMEOUT,
            SSMI_USSD_TYPE_END,
        ]
        
        if ussd_type in routes:
            self.queue.send({
                'msisdn': msisdn,
                'ussd_type': ussd_type,
                'ussd_phase': ussd_phase,
                'message': message,
            })
        else:
            log.err('FATAL: No handler available for ussd type %s' % ussd_type)
    

    

class Options(usage.Options):
    optParameters = [
        ["ssmi-username", None, None, "SSMI username"],
        ["ssmi-password", None, None, "SSMI password"],
        ["ssmi-host", None, None, "SSMI host"],
        ["ssmi-port", None, None, "SSMI host's port"],
        ["amqp-host", None, "localhost", "AMQP host"],
        ["amqp-port", None, "5672", "AMQP port"],
        ["amqp-username", None, "richmond", "AMQP username"],
        ["amqp-password", None, "richmond", "AMQP password"],
        ["amqp-vhost", None, "/richmond", "AMQP virtual host"],
        ["amqp-feed", None, "richmond", "AMQP feed"],
        ["amqp-exchange", None, "richmond", "AMQP exchange"],
        ["amqp-receive-routing-key", None, "ssmi.ussd.receive", "AMQP incoming routing key"],
        ["amqp-send-routing-key", None, "ssmi.ussd.send", "AMQP outgoing routing key"],
    ]


class SSMIServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "amqp"
    description = "Connect SSMI to AMQP bus"
    options = Options
    
    def makeService(self, options):
        # all are mandatory, if they haven't been provided, prompt for them
        for key in options:
            if not options[key]:
                options[key] = getpass('%s: ' % key)
        
        connection = BrokerConnection(hostname=options['amqp-host'], 
                                port=int(options['amqp-port']),
                                userid=options['amqp-username'],
                                password=options['amqp-password'],
                                virtual_host=options['amqp-vhost'])
        
        publisher = Publisher(connection=connection,
                                exchange=options["amqp-exchange"],
                                routing_key=options["amqp-send-routing-key"])
        
        consumer = Consumer(connection=connection,
                                exchange=options["amqp-exchange"],
                                routing_key=options["amqp-receive-routing-key"])
        
        ssmi_service = SSMIService(options['ssmi-username'], 
                                    options['ssmi-password'], publisher)
        
        def handle_message(data, message):
            logging.debug("inlineCallback received: %s" % str(data))
            ssmi_service.send_ussd(data['msisdn'], data['message'], data['ussd_type'])
            message.ack()
        
        # consumer.register_callback(handle_message)
        # 
        # @defer.inlineCallbacks
        # def synchronouse_consumer_loop(consumer):
        #     for message in consumer.iterconsume():
        #         yield message
        
        def app_register(ssmi_protocol):
            return ssmi_service.register_ssmi(ssmi_protocol)
        
        # d = defer.Deferred()
        # d.addCallback(synchronouse_consumer_loop)
        # reactor.callLater(3, d.callback, consumer)
        
        # # FIXME: ooh my, I don't like the look of txamqp
        # delegate = TwistedDelegate()
        # d = ClientCreator(reactor, AMQClient, delegate=delegate, 
        #                     vhost=options["amqp-vhost"],spec=spec)\
        #                     .connectTCP(options["amqp-host"], options["amqp-port"])
        # d.addCallback(gotConnection, options["amqp-username"], options["amqp-password"])
        # 
        return internet.TCPClient(options['ssmi-host'], int(options['ssmi-port']), 
                            SSMIFactory(app_register_callback=app_register))


serviceMaker = SSMIServiceMaker()