import ConfigParser

from twisted.application.service import Service, MultiService
from twisted.python import log
from twisted.python.log import logging
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred

import txamqp.spec

from vumi.amqp.base import VumiAMQPFactory
from vumi.errors import VumiError

class AMQPService(Service):
    
    username = 'vumi'
    password = 'vumi'
    host = 'localhost'
    port = 5672
    vhost = '/vumi'
    spec = 'config/amqp-spec-0-8.xml'
    
    def __init__(self, **options):
        self.username = options.get('username', self.username)
        self.password = options.get('password', self.password)
        self.host = options.get('host', self.host)
        self.port = int(options.get('port', self.port))
        self.vhost = options.get('vhost', self.vhost)
        self.spec = options.get('spec', self.spec)
        
        self.onConnectionMade = Deferred()
        self.onConnectionLost = Deferred()
        
        # NOTE: order is important
        self.onConnectionMade.addCallback(self.authenticate)
        self.onConnectionMade.addErrback(lambda f: f.raiseException())
        
        # we're using a ReconnectingClient
        self.onConnectionLost.addErrback(lambda f: f.raiseException())
    
    @inlineCallbacks
    def authenticate(self, client):
        yield client.authenticate(self.username, self.password)
        log.msg("Authenticated user %s" % self.username)
        returnValue(client)
    
    def startService(self):
        factory = VumiAMQPFactory(self.spec, self.vhost)
        # attach deferreds so we can keep track of (dis)connections and
        # start services as needed
        factory.onConnectionMade = self.onConnectionMade
        factory.onConnectionLost = self.onConnectionLost
        reactor.connectTCP(self.host, self.port, factory)
        log.msg("Starting AMQP service")
    
    def stopService(self):
        log.msg("Stopping AMQP service")
    

class VumiService(MultiService):
    """
    A base Service class that we can subclass, should contain all the AMQP
    boilerplate
    """
    def __init__(self, config_file, **kwargs):
        MultiService.__init__(self)
        # read the config file first
        self.config_file = config_file
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(open(config_file))
        
        amqp_options = self.get_config('amqp')
        # filter out blank values
        amqp_options = dict([(key,value) \
                                for key, value in amqp_options.items() \
                                if value])
        amqp_service = AMQPService(**amqp_options)
        amqp_service.onConnectionMade.addCallback(self.on_connect)
        amqp_service.onConnectionLost.addCallback(self.on_disconnect)
        self.addService(amqp_service)
        self.amqp_client = None
    
    def get_config(self, section):
        if self.config.has_section(section):
            return dict((option, self.config.get(section, option))
                        for option in self.config.options(section))
        else:
            return {}
    
    @inlineCallbacks
    def on_connect(self, client):
        log.msg("VumiService connected %s" % client)
        self.amqp_client = client
        yield self.start(**self.get_config('service'))
        returnValue(client)
    
    @inlineCallbacks
    def on_disconnect(self, client):
        log.msg("VumiService disconnected %s" % client)
        self.amqp_client = None
        yield self.stop()
        returnValue(client)
    
    def ensure_amqp_service_is_ready(self):
        if not self.amqp_client:
            raise VumiError, "No amqp_client available. AMQPService " \
                                    "either not connected yet or it has " \
                                    "lost the connection to the broker."
        
    
    @inlineCallbacks
    def create_consumer(self, klass, *args, **kwargs):
        self.ensure_amqp_service_is_ready()
        consumer = klass(*args, **kwargs)
        consumer.set_amq_client(self.amqp_client)
        yield consumer.join_queue(exchange_name=consumer.exchange_name, 
                            exchange_type=consumer.exchange_type, 
                            queue_name=consumer.queue_name, 
                            routing_key=consumer.routing_key)
        yield consumer.start()
        returnValue(consumer)
    
    @inlineCallbacks
    def create_publisher(self, klass, *args, **kwargs):
        self.ensure_amqp_service_is_ready()
        publisher = klass(*args, **kwargs)
        publisher.set_amq_client(self.amqp_client)
        yield publisher.publish_to(publisher.exchange_name,
                                    publisher.routing_key)
        returnValue(publisher)
    
    def start(self):
        pass
    
    def stop(self):
        pass