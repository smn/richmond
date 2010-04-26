from zope.interface import implements
from getpass import getpass

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application import internet
from twisted.application.service import IServiceMaker

from ssmi.client import SSMIFactory
from ssmi.client import (SSMI_USSD_TYPE_NEW, SSMI_USSD_TYPE_EXISTING, 
                            SSMI_USSD_TYPE_END, SSMI_USSD_TYPE_TIMEOUT)
import logging

from carrot.connection import BrokerConnection
from carrot.messaging import Publisher


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
            
    
    def reply(self, msisdn, text, reply_type):
        return self.ssmi_client.send_ussd(msisdn, text, reply_type)
    
    def process_sms(self, *args):
        """Process an SMS message received in reply to an SMS we sent out."""
        pass
    
    def new_ussd_session(self, msisdn, message):
        self.reply(msisdn, "Hello, this is an echo service for testing. "
                            "Reply with whatever. Reply 'quit' to end session.", 
                            SSMI_USSD_TYPE_EXISTING)
        self.queue.send({
            "type": SSMI_USSD_TYPE_NEW,
            "message": message,
            "msisdn": msisdn,
        })
    
    def existing_ussd_session(self, msisdn, message):
        message = message.strip()
        
        self.queue.send({
            "type": SSMI_USSD_TYPE_EXISTING,
            "message": message,
            "msisdn": msisdn,
        })
        
        if message == "quit":
            self.reply(msisdn, "quitting, goodbye!", SSMI_USSD_TYPE_END)
        else:
            self.reply(msisdn, message, SSMI_USSD_TYPE_EXISTING)
    
    def timed_out_ussd_session(self, msisdn, message):
        logging.debug('%s timed out, removing client' % msisdn)
        self.queue.send({
            "type": SSMI_USSD_TYPE_TIMEOUT,
            "message": message,
            "msisdn": msisdn,
        })
        
    
    def end_ussd_session(self, msisdn, message):
        logging.debug('%s ended the session, removing client' % msisdn)
        self.queue.send({
            "type": SSMI_USSD_TYPE_END,
            "message": message,
            "msisdn": msisdn,
        })
        
    
    def process_ussd(self, msisdn, ussd_type, ussd_phase, message):
        if self.ssmi_client is None:
            log.err('FATAL: client not registered')
            return
        
        routes = {
            SSMI_USSD_TYPE_NEW: self.new_ussd_session,
            SSMI_USSD_TYPE_EXISTING: self.existing_ussd_session,
            SSMI_USSD_TYPE_TIMEOUT: self.timed_out_ussd_session,
            SSMI_USSD_TYPE_END: self.end_ussd_session
        }
        
        handler = routes[ussd_type]
        if handler:
            handler(msisdn, message)
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
        ["amqp-username", None, "guest", "AMQP username"],
        ["amqp-password", None, "guest", "AMQP password"],
        ["amqp-vhost", None, "richmond", "AMQP virtual host"],
        ["amqp-feed", None, "richmond", "AMQP feed"],
        ["amqp-exchange", None, "richmond", "AMQP exchange"],
        ["amqp-routing-key", None, "ssmi", "AMQP routing key"],
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
                                routing_key=options["amqp-routing-key"])
        
        def app_register(ssmi_protocol):
            return SSMIService(options['ssmi-username'], 
                                options['ssmi-password'],
                                publisher) \
                                .register_ssmi(ssmi_protocol)
        
        return internet.TCPClient(options['ssmi-host'], int(options['ssmi-port']), 
                            SSMIFactory(app_register_callback=app_register))


serviceMaker = SSMIServiceMaker()