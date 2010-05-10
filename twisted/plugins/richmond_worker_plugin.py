from zope.interface import implements

import txamqp.spec
from txamqp.content import Content
from txamqp.protocol import AMQClient
from txamqp.client import TwistedDelegate
from txamqp.queue import Empty

from twisted.python import usage, log
from twisted.python.log import logging
from twisted.internet import error, protocol, reactor, defer
from twisted.internet.defer import inlineCallbacks, Deferred, returnValue
from twisted.application.service import IServiceMaker, MultiService, Application
from twisted.application import internet
from twisted.plugin import IPlugin
import json

from richmond.service import ssmi_service
from richmond.service import amqp_service
from richmond.utils import filter_options_on_prefix, load_class_by_string

from ssmi.client import SSMI_USSD_TYPE_END, SSMI_USSD_TYPE_NEW

class Options(usage.Options):
    optParameters = [
        ["config", "c", None, "Read options from config file"],
        ["amqp-host", None, "localhost", "AMQP host"],
        ["amqp-port", None, 5672, "AMQP port", int],
        ["amqp-username", None, "richmond", "AMQP username"],
        ["amqp-password", None, "richmond", "AMQP password"],
        ["amqp-spec", None, "config/amqp-spec-0-8.xml", "AMQP spec file"],
        ["amqp-vhost", None, "/richmond", "AMQP virtual host"],
        ["amqp-ussd-send-queue", None, "richmond.send", "AMQP send queue"],
        ["amqp-ussd-send-routing-key", None, "ussd.send", "AMQP routing key"],
        ["amqp-exchange", None, "richmond", "AMQP exchange"],
        ["amqp-exchange-type", None, "direct", "AMQP exchange type"],
        ["amqp-ussd-receive-queue", None, "richmond.ussd.receive", "AMQP receive queue"],
        ["amqp-ussd-receive-routing-key", None, "ussd.receive", "AMQP routing key"],
        ["amqp-ussd-worker-class", "w", "richmond.workers.base.RichmondWorker", "AMQP worker class"]
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


class RichmondWorkerServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "richmond_worker"
    description = "Connect to AMQP broker and start working jobs"
    options = Options
    
    def get_amqp_options(self, options):
        return filter_options_on_prefix(options, "amqp")
    
    def makeService(self, options):
        amqp_options = self.get_amqp_options(options)
        worker_class = load_class_by_string(amqp_options['ussd-worker-class'])
        
        amqp_srv = amqp_service.AMQPService(amqp_options['host'],
                                            amqp_options['port'],
                                            amqp_options['username'],
                                            amqp_options['password'],
                                            amqp_options['spec'],
                                            amqp_options['vhost'],
                                            consumer_class=worker_class
                                            )
        @defer.inlineCallbacks
        def consumer_ready(amq_client):
            yield amqp_srv.consumer.join_queue(
                                        amqp_options['exchange'],
                                        amqp_options['exchange-type'],
                                        amqp_options['ussd-receive-queue'],
                                        amqp_options['ussd-receive-routing-key'])
            defer.returnValue(amq_client)
    
        @defer.inlineCallbacks
        def publisher_ready(amq_client):
            yield amqp_srv.publisher.publish_to(
                            exchange=amqp_options['exchange'],
                            routing_key=amqp_options['ussd-send-routing-key'])
            yield amqp_srv.consumer.set_publisher(amqp_srv.publisher)
            yield amqp_srv.consumer.start()
            defer.returnValue(amq_client)
    
        amqp_srv.onConnectionMade.addCallback(consumer_ready)
        amqp_srv.onConnectionMade.addCallback(publisher_ready)
        return amqp_srv

serviceMaker = RichmondWorkerServiceMaker()
