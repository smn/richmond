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
from richmond.amqp.base import AMQPConsumer
from richmond.utils import filter_options_on_prefix

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


class RichmondWorker(AMQPConsumer):
    publisher = None
    def set_publisher(self, publisher):
        log.msg("RichmondWorker will publish to: %s" % publisher)
        self.publisher = publisher
    
    def publish(self, data):
        self.publisher.send(data)
    
    def consume(self, data):
        if data['ussd_type'] == SSMI_USSD_TYPE_NEW:
            self.publish({
                "msisdn": data['msisdn'],
                "message": "so long and thanks for all the fish",
                "ussd_type": SSMI_USSD_TYPE_END
            })
        else:
            log.msg("Ignore message: %s" % data)
    
    def ack(self, message):
        self.channel.basic_ack(message.delivery_tag, True)
    
    def start(self):
        if self.publisher:
            super(RichmondWorker, self).start()
        else:
            raise RuntimeException, """This consumer cannot start without having been assigned a publisher first."""
    
    def consume_data(self, message):
        self.consume(json.loads(message.content.body))
        self.ack(message)
            


class RichmondWorkerServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "richmond_worker"
    description = "Connect to AMQP broker and start working jobs"
    options = Options
    
    def get_amqp_options(self, options):
        return filter_options_on_prefix(options, "amqp")
    
    def makeService(self, options):
        amqp_options = self.get_amqp_options(options)
        
        amqp_srv = amqp_service.AMQPService(amqp_options['host'],
                                            amqp_options['port'],
                                            amqp_options['username'],
                                            amqp_options['password'],
                                            amqp_options['spec'],
                                            amqp_options['vhost'],
                                            consumer_class=RichmondWorker
                                            )
        @defer.inlineCallbacks
        def consumer_ready(amq_client):
            yield amqp_srv.consumer.join_queue(
                                        amqp_options['exchange'],
                                        "direct",
                                        amqp_options['receive-queue'],
                                        amqp_options['receive-routing-key'])
            defer.returnValue(amq_client)
    
        @defer.inlineCallbacks
        def publisher_ready(amq_client):
            yield amqp_srv.publisher.publish_to(
                            exchange=amqp_options['exchange'],
                            routing_key=amqp_options['send-routing-key'])
            yield amqp_srv.consumer.set_publisher(amqp_srv.publisher)
            yield amqp_srv.consumer.start()
            defer.returnValue(amq_client)
    
        amqp_srv.onConnectionMade.addCallback(consumer_ready)
        amqp_srv.onConnectionMade.addCallback(publisher_ready)
        return amqp_srv

serviceMaker = RichmondWorkerServiceMaker()
