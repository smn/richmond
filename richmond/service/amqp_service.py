from zope.interface import implements
import logging
import json

import txamqp.spec
from txamqp.client import TwistedDelegate
from txamqp.protocol import AMQClient
from txamqp.content import Content

from twisted.python import log
from twisted.internet import reactor, defer, protocol
from twisted.application.service import IServiceMaker, Service

# AMQP Channels are stateful, to make sure we don't get any scary
# bugs because of two separate instances using the same channel we split them
CONSUMER_CHANNEL_ID = 1
PUBLISHER_CHANNEL_ID = 2

class RichmondAMQClient(AMQClient):
    """
    Subclassed AMQClient to allow for deferred callbacks on connectionMade and
    connectionLost events
    """
    def connectionMade(self, *args, **kwargs):
        AMQClient.connectionMade(self, *args, **kwargs)
        self.factory.onConnectionMade.callback(self)
    
    def connectionLost(self, *args, **kwargs):
        AMQClient.connectionLost(self, *args, **kwargs)
        self.factory.onConnectionLost.callback(self)
    


@defer.inlineCallbacks
def open_channel(client, channel_id):
    """
    Open a channel for the given client with the given channel id. The
    channel_id's should be integers. Not sure why, some txamqp magic.
    """
    log.msg("Opening channel with id %s" % channel_id, logLevel=logging.DEBUG)
    channel = yield client.channel(channel_id)
    yield channel.channel_open()
    log.msg("Channel %s opened" % channel_id, logLevel=logging.DEBUG)
    defer.returnValue(channel)


@defer.inlineCallbacks
def join_queue(client, channel, exchange_name, exchange_type, queue_name, 
                routing_key, durable=False):
    log.msg("Joining queue '%s' with routing key '%s'" % 
                            (queue_name, routing_key), logLevel=logging.DEBUG)
    yield channel.queue_declare(queue=queue_name, durable=durable)
    log.msg("Declared queue %s, durable?: %s" % (queue_name, durable), 
                                                    logLevel=logging.DEBUG)
    yield channel.exchange_declare(exchange=exchange_name, 
                                        type=exchange_type,
                                        durable=durable)
    log.msg("Connected to exchange '%s' of type '%s'" % 
                                                (exchange_name, exchange_type),
                                                logLevel=logging.DEBUG)
    yield channel.queue_bind(queue=queue_name, exchange=exchange_name, 
                                routing_key=routing_key)
    log.msg("Bound '%s' to exchange '%s' with routing key '%s'" % 
                                (queue_name, exchange_name, routing_key), 
                                logLevel=logging.DEBUG)
    
    reply = yield channel.basic_consume(queue=queue_name)
    log.msg("Registered the consumer for queue '%s'" % queue_name, 
                                                logLevel=logging.DEBUG)
    queue = yield client.queue(reply.consumer_tag)
    defer.returnValue(queue)


class AMQPConsumer(object):
    
    shutdown = False
    
    def __init__(self, amq_client):
        """Start the consumer"""
        self.amq_client = amq_client
        log.msg("Started AMQPConsumer")
    
    @defer.inlineCallbacks
    def join_queue(self, exchange_name, exchange_type, queue_name, routing_key):
        """
        join the named queue with the given routing key attached
        to the given exchange
        """
        self.queue_name = queue_name
        self.routing_key = routing_key
        self.channel = yield open_channel(self.amq_client, CONSUMER_CHANNEL_ID)
        queue = yield join_queue(self.amq_client, self.channel, exchange_name,
                                    exchange_type, queue_name, routing_key)
        log.msg("Got a queue: %s" % queue, logLevel=logging.DEBUG)
        
        def read_messages():
            while not shutdown:
                log.msg("Waiting for messages")
                message = yield queue.get()
                self.consume_data(message)
        read_messages()
        defer.returnValue(self)
    
    def consume_data(self, message):
        log.msg("Received data: '%s' but doing nothing" % message.content.body, 
                                        logLevel=logging.DEBUG)
        self.channel.basic_ack(message.delivery_tag, True)
    


class AMQPPublisher(object):
    
    def __init__(self, amq_client):
        """Start the publisher"""
        self.amq_client = amq_client
    
    @defer.inlineCallbacks
    def publish_to(self, exchange, routing_key):
        """publish to the exchange with the given routing key"""
        self.exchange = exchange
        self.routing_key = routing_key
        self.channel = yield open_channel(self.amq_client, PUBLISHER_CHANNEL_ID)
        log.msg("Ready to publish to exchange '%s' with routing key '%s'" % (
            self.exchange, self.routing_key), logLevel=logging.DEBUG)
    
    def send(self, data):
        log.msg("Publishing '%s' to exchange '%s' with routing key '%s'" % (
            data, self.exchange, self.routing_key))
        self.channel.basic_publish(exchange=self.exchange, 
                                        content=Content(json.dumps(data)), 
                                        routing_key=self.routing_key)
        
    


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
    
