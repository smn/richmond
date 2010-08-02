from twisted.python import log, usage
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from twisted.internet import protocol
from txamqp.client import TwistedDelegate
from txamqp.content import Content
from txamqp.protocol import AMQClient
import txamqp
import json
import sys

class Options(usage.Options):
    optParameters = [
        ["hostname", None, "127.0.0.1", "AMQP broker"],
        ["port", None, 5672, "AMQP port", int],
        ["username", None, "richmond", "AMQP username"],
        ["password", None, "richmond", "AMQP password"],
        ["vhost", None, "/richmond", "AMQP virtual host"],
        ["specfile", None, "config/amqp-spec-0-8.xml", "AMQP spec file"],
    ]


class Worker(AMQClient):
    
    def connectionMade(self):
        AMQClient.connectionMade(self)
        deferred = self.authenticate(self.factory.username, self.factory.password)
        deferred.addCallback(self.authenticated)
        deferred.addErrback(log.err)
    
    @inlineCallbacks
    def authenticated(self, ignore):
        log.msg("Got an authenticated connection")
        yield self.startWorker()
    
    @inlineCallbacks
    def get_channel(self, channel_id=None):
        """If channel_id is None a new channel is created"""
        if channel_id:
            channel = self.channels[channel_id]
        else:
            channel_id = self.get_new_channel_id()
            channel = yield self.channel(channel_id)
            yield channel.channel_open()
            self.channels[channel_id] = channel
        returnValue(channel)
    
    def get_new_channel_id(self):
        return (max(self.channels) + 1) if self.channels else 0
    
    @inlineCallbacks
    def start_consumer(self, klass, *args, **kwargs):
        channel = yield self.get_channel()
        consumer = klass(*args, **kwargs)
        
        exchange_name = consumer.exchange_name
        exchange_type = consumer.exchange_type
        durable = consumer.durable
        
        queue_name = consumer.queue_name
        routing_key = consumer.routing_key
        
        # declare the exchange, doesn't matter if it already exists
        yield channel.exchange_declare(exchange=exchange_name,
                                        type=exchange_type, durable=durable)
                                                    
        # declare the queue
        yield channel.queue_declare(queue=queue_name, durable=durable)
        # bind it to the exchange with the routing key
        yield channel.queue_bind(queue=queue_name, exchange=exchange_name, 
                                    routing_key=routing_key)
        # register the consumer
        reply = yield channel.basic_consume(queue=queue_name)
        queue = yield self.queue(reply.consumer_tag)
        consumer.start(channel, queue)
        returnValue(consumer)
    
    @inlineCallbacks
    def start_publisher(self, klass, *args, **kwargs):
        channel = yield self.get_channel()
        publisher = klass(*args, **kwargs)
        yield publisher.start(channel)
        returnValue(publisher)
    

class Consumer(object):
    
    exchange_name = "richmond"
    exchange_type = "direct"
    durable = False
    
    queue_name = "queue"
    routing_key = "routing_key"
    
    def __init__(self):
        """Start the consumer"""
        pass
    
    @inlineCallbacks
    def start(self, channel, queue):
        log.msg("Started consumer with publisher: %s" % self.publisher)
        self.channel = channel
        self.queue = queue
        @inlineCallbacks
        def read_messages():
            log.msg("Consumer starting...")
            try:
                while True:
                    message = yield self.queue.get()
                    self.raw_consume(message)
            except txamqp.queue.Closed, e:
                log.err("Queue has closed: %s" % e)
        read_messages()
        yield None
        returnValue(self)
    
    def raw_consume(self, message):
        self.consume_json(json.loads(message.content.body))
        self.ack(message)
    
    def consume_json(self, dictionary):
        log.msg("Received dict: %s" % dictionary)
    
    def ack(self, message):
        self.channel.basic_ack(message.delivery_tag, True)
    

class Publisher(object):
    exchange_name = "richmond"
    exchange_type = "direct"
    routing_key = "routing_key"
    durable = False
    auto_delete = False
    delivery_mode = 2 # save to disk
    
    def start(self, channel):
        log.msg("Started the publisher")
        self.channel = channel
    
    def publish(self, data):
        message = Content(json.dumps(data))
        message['delivery mode'] = self.delivery_mode
        self.channel.basic_publish(exchange=self.exchange_name, 
                                        content=message, 
                                        routing_key=self.routing_key)


class AmqpFactory(protocol.ReconnectingClientFactory):
    
    def __init__(self, specfile, vhost, username, password, worker_class, **options):
        self.username = username
        self.password = password
        self.vhost = vhost
        self.spec = txamqp.spec.load(specfile)
        self.delegate = TwistedDelegate()
        self.worker_class = worker_class
        self.options = options
        print 'options', options
    
    def buildProtocol(self, addr):
        worker = self.worker_class(self.delegate, self.vhost, self.spec)
        worker.factory = self
        self.worker = worker
        self.resetDelay()
        return worker
    
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed."
        self.worker.stopWorker()
        protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
    
    def clientConnectionLost(self, connector, reason):
        print "Client connection lost."
        self.worker.stopWorker()
        protocol.ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
    

class WorkerCreator(object):
    
    def __init__(self, reactor, worker_class, *args, **kwargs):
        self.reactor = reactor
        self.args = args
        self.kwargs = kwargs
        self.kwargs.update({
            'worker_class': worker_class
        })
    
    def connectTCP(self, host, port, timeout=30, bindAddress=None):
        factory = AmqpFactory(*self.args, **self.kwargs)
        self.reactor.connectTCP(host, port, factory, timeout=timeout, bindAddress=bindAddress)
