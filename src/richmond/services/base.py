from twisted.application.service import Service, MultiService
from twisted.python import log
from twisted.python.log import logging
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred

import txamqp.spec

from richmond.amqp.base import RichmondAMQPFactory
from richmond.errors import RichmondError

class AMQPService(Service):
    
    host = 'localhost'
    port = 5672
    vhost = '/richmond'
    spec = 'config/amqp-spec-0-8.xml'
    
    def __init__(self, username, password, **options):
        self.username = username
        self.password = password
        self.host = options.get('host', self.host)
        self.port = options.get('port', self.port)
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
        factory = RichmondAMQPFactory(self.spec, self.vhost)
        # attach deferreds so we can keep track of (dis)connections and
        # start services as needed
        factory.onConnectionMade = self.onConnectionMade
        factory.onConnectionLost = self.onConnectionLost
        reactor.connectTCP(self.host, self.port, factory)
        log.msg("Starting AMQP service")
    
    def stopService(self):
        log.msg("Stopping AMQP service")
    

class RichmondService(MultiService):
    """
    A base Service class that we can subclass, should contain all the AMQP
    boilerplate
    """
    def __init__(self, *args, **kwargs):
        MultiService.__init__(self)
        amqp_service = AMQPService(**kwargs)
        amqp_service.onConnectionMade.addCallback(self.on_connect)
        amqp_service.onConnectionLost.addCallback(self.on_disconnect)
        self.addService(amqp_service)
        self.amqp_client = None
    
    @inlineCallbacks
    def on_connect(self, client):
        log.msg("RichmondService connected %s" % client)
        self.amqp_client = client
        yield self.start()
        returnValue(client)
    
    @inlineCallbacks
    def on_disconnect(self, client):
        log.msg("RichmondService disconnected %s" % client)
        self.amqp_client = None
        yield self.stop()
        returnValue(client)
    
    def ensure_amqp_service_is_ready(self):
        if not self.amqp_client:
            raise RichmondError, "No amqp_client available. AMQPService " \
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