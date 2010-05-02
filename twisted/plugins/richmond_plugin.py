from zope.interface import implements

import txamqp.spec
from txamqp.content import Content
from txamqp.protocol import AMQClient
from txamqp.client import TwistedDelegate
from txamqp.queue import Empty

from twisted.python import usage, log
from twisted.internet import error, protocol, reactor
from twisted.internet.defer import inlineCallbacks, Deferred, returnValue
from twisted.application.service import IServiceMaker, MultiService, Application
from twisted.application import internet
from twisted.plugin import IPlugin
import json

from richmond.service import ssmi_service
from richmond.service import amqp_service
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


class MockedQueue(object):
    def send(self, data):
        log.msg("Publishing %s to the queue." % str(data))

class USSDCallback(ssmi_service.SSMICallback):
    
    queue = MockedQueue()
    
    def ussd_callback(self, msisdn, ussd_type, ussd_phase, message):
        self.queue.send({
                'msisdn': msisdn,
                'ussd_type': ussd_type,
                'ussd_phase': ussd_phase,
                'message': message,
            })

class RichmondServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "richmond"
    description = "Connect to SSMI to AMQP broker"
    options = Options
    
    def get_amqp_options(self, options):
        return filter_options_on_prefix(options, "amqp")
    
    def get_ssmi_options(self, options):
        return filter_options_on_prefix(options, "ssmi")
    
    def makeService(self, options):
        
        ssmi_options = self.get_ssmi_options(options)
        amqp_options = self.get_amqp_options(options)
        
        multi_service = MultiService()
        
        amqp_srv = amqp_service.AMQPService(amqp_options['host'],
                                            amqp_options['port'],
                                            amqp_options['username'],
                                            amqp_options['password'],
                                            amqp_options['spec'],
                                            amqp_options['vhost'],
                                            )
        amqp_srv.setServiceParent(multi_service)
        
        def start_consumer(ssmi_client):
            amqp_srv.consumer.join_channel("some queue", "bound to some routing.key")
        
        def start_publisher(ssmi_client):
            amqp_srv.publisher.publish_to("some exchange", "with some routing.key")
            ssmi_client.publish_to(amqp_srv.publisher)
        
        ssmi_srv = ssmi_service.SSMIService(ssmi_options['username'], 
                                            ssmi_options['password'],
                                            ssmi_options['host'], 
                                            ssmi_options['port'],
                                            USSDCallback)
        ssmi_srv.setServiceParent(multi_service)
        
        # start amqp consumer & publisher after we've successfully connected
        # to the SSMI gateway
        ssmi_srv.onConnectionMade.addCallback(start_consumer)
        ssmi_srv.onConnectionMade.addCallback(start_publisher)
        
        return multi_service

serviceMaker = RichmondServiceMaker()
