import json

from twisted.internet import defer, protocol
from twisted.python import log
from twisted.python.log import logging

import txamqp.spec
from txamqp.client import TwistedDelegate
from txamqp.protocol import AMQClient
from txamqp.content import Content

from richmond.amqp.utils import open_channel, join_queue

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
    


class AMQPConsumer(object):
    
    shutdown = False
    
    def __init__(self, amq_client):
        """Start the consumer"""
        self.amq_client = amq_client
        log.msg("Started consumer")
    
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
        message = Content(json.dumps(data))
        message['delivery mode'] = 2
        self.channel.basic_publish(exchange=self.exchange, 
                                        content=message, 
                                        routing_key=self.routing_key)
        
    


class RichmondAMQPFactory(protocol.ClientFactory):
    
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


