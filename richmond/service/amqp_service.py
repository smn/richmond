from zope.interface import implements

from twisted.python import log
from twisted.python.log import logging
from twisted.internet import reactor, defer
from twisted.application.service import IServiceMaker, Service

from richmond.amqp.base import AMQPConsumer, AMQPPublisher, RichmondAMQPFactory

class AMQPService(Service):
    implements(IServiceMaker)
    
    def __init__(self, host, port, username, password, vhost, spec,
                consumer_class=AMQPConsumer, publisher_class=AMQPPublisher):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.vhost = vhost
        self.spec = spec
        self.onConnectionMade = defer.Deferred()
        
        # NOTE: order is important
        self.onConnectionMade.addCallback(self.authenticate)
        self.onConnectionMade.addCallback(self.start_consumer)
        self.onConnectionMade.addCallback(self.start_publisher)
        self.onConnectionMade.addErrback(lambda f: f.raiseException())
        
        # we're using a ReconnectingClient
        self.onConnectionLost = defer.Deferred()
        self.onConnectionLost.addErrback(lambda f: f.raiseException())
        
    
    def authenticate(self, client):
        client.authenticate(self.username, self.password)
        log.msg("Authenticated user %s" % self.username)
        return client
    
    def start_consumer(self, client):
        self.consumer = AMQPConsumer(client)
        return client
    
    def start_publisher(self, client):
        self.publisher = AMQPPublisher(client)
        return client
    
    def startService(self):
        factory = RichmondAMQPFactory(self.vhost, self.spec)
        
        # attach deferreds so we can keep track of (dis)connections and
        # start services as needed
        factory.onConnectionMade = self.onConnectionMade
        factory.onConnectionLost = self.onConnectionLost
        
        self.client_connection = reactor.connectTCP(self.host, self.port, factory)
        log.msg("starting amqp service")
    
    def stopService(self):
        self.client_connection.disconnect()
        log.msg("stopping amqp service")
    
