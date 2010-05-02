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
        self.onConnectionLost = defer.Deferred()
    
    def authenticate(self, client):
        client.authenticate(self.username, self.password)
        return client
    
    def start_consumer(self, client):
        log.msg("starting consumer for: %s" % client)
        return client
    
    def start_publisher(self, client):
        log.msg("start publisher for: %s" % client)
        return client
    
    def startService(self):
        factory = RichmondAMQPFactory(*self.args, **self.kwargs)
        factory.onConnectionMade = self.onConnectionMade
        factory.onConnectionLost = self.onConnectionLost
        factory.onConnectionMade.addCallback(self.authenticate)
        factory.onConnectionMade.addCallback(self.start_consumer)
        factory.onConnectionMade.addCallback(self.start_publisher)
        self.client_connection = reactor.connectTCP(self.host, self.port, factory)
        log.msg("starting amqp service")
    
    def stopService(self):
        self.client_connection.disconnect()
        log.msg("stopping amqp service")
    
