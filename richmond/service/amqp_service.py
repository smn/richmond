from zope.interface import implements
import logging

import txamqp.spec
from txamqp.client import TwistedDelegate
from txamqp.protocol import AMQClient

from twisted.python import log
from twisted.internet import reactor, defer, protocol
from twisted.application.service import IServiceMaker, Service

class RichmondAMQClient(AMQClient):
    
    def connectionMade(self, *args, **kwargs):
        AMQClient.connectionMade(self, *args, **kwargs)
        self.factory.onConnectionMade.callback(self)
    
    def connectionLost(self, *args, **kwargs):
        AMQClient.connectionLost(self, *args, **kwargs)
        self.factory.onConnectionLost.callback(self)
    

class RichmondAMQPFactory(protocol.ReconnectingClientFactory):
    
    protocol = RichmondAMQClient
    
    def __init__(self, spec, vhost):
        self.delegate = TwistedDelegate()
        self.spec = txamqp.spec.load(spec)
        self.vhost = vhost
    
    def buildProtocol(self, addr):
        prot = self.protocol(self.delegate, self.vhost, self.spec)
        prot.factory = self
        log.msg("RichmondAMQPFactory connected.", logLevel=logging.DEBUG)
        return prot
    


class AMQPConsumer(object):
    
    def __init__(self, amq_client):
        """Start the consumer"""
        self.amq_client = amq_client
        log.msg("Started AMQPConsumer")
    
    def join_queue(self, queue_name, routing_key):
        """
        join the named queue with the given routing key attached
        to the given exchange
        """
        self.queue_name = queue_name
        self.routing_key = routing_key
        log.msg("Joining queue '%s' with routing key '%s'" % (queue_name, routing_key))
    


class AMQPPublisher(object):
    
    def __init__(self, amq_client):
        """Start the publisher"""
        self.amq_client = amq_client
        log.msg("Started AMQPPublisher")
    
    def publish_to(self, exchange, routing_key):
        """publish to the exchange with the given routing key"""
        self.exchange = exchange
        self.routing_key = routing_key
        log.msg("Ready to publish to exchange '%s' with routing key '%s'" % (
            self.exchange, self.routing_key))
    
    def send(self, data):
        log.msg("Publishing '%s' to exchange '%s' with routing key '%s'" % (
            data, self.exchange, self.routing_key))
    



class AMQPService(Service):
    implements(IServiceMaker)
    
    def __init__(self, host, port, username, password, *args, **kwargs):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.args = args
        self.kwargs = kwargs
        self.onConnectionMade = defer.Deferred()
        
        # NOTE: order is important
        self.onConnectionMade.addCallback(self.authenticate)
        self.onConnectionMade.addCallback(self.start_consumer)
        self.onConnectionMade.addCallback(self.start_publisher)
        
        self.onConnectionLost = defer.Deferred()
        
    
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
        factory = RichmondAMQPFactory(*self.args, **self.kwargs)
        
        # attach deferreds so we can keep track of (dis)connections and
        # start services as needed
        factory.onConnectionMade = self.onConnectionMade
        factory.onConnectionLost = self.onConnectionLost
        
        self.client_connection = reactor.connectTCP(self.host, self.port, factory)
        log.msg("starting amqp service")
    
    def stopService(self):
        self.client_connection.disconnect()
        log.msg("stopping amqp service")
    
