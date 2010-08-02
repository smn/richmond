from zope.interface import implements
from twisted.python import usage, log
from twisted.application.service import IServiceMaker, Service
from twisted.plugin import IPlugin
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import reactor, protocol

from richmond.utils import filter_options_on_prefix

from txamqp.protocol import AMQClient
from txamqp.client import TwistedDelegate
from txamqp.content import Content
import txamqp
import json

class Options(usage.Options):
    optParameters = [
        ["amqp-hostname", None, "127.0.0.1", "AMQP broker"],
        ["amqp-port", None, 5672, "AMQP port", int],
        ["amqp-username", None, "richmond", "AMQP username"],
        ["amqp-password", None, "richmond", "AMQP password"],
        ["amqp-vhost", None, "/richmond", "AMQP virtual host"],
        ["amqp-specfile", None, "config/amqp-spec-0-8.xml", "AMQP spec file"],
        ["service", "s", None, "The Richmond service class to start"]
    ]

class AmqpProtocol(AMQClient):
    
    def connectionMade(self):
        AMQClient.connectionMade(self)
        deferred = self.authenticate(self.factory.username, self.factory.password)
        deferred.addCallback(self.authenticated)
        deferred.addErrback(log.err)
    
    @inlineCallbacks
    def authenticated(self, ignore):
        log.msg("Got an authenticated connection")
        yield self.start_service()
    
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
    
    def __init__(self, publisher):
        """Start the consumer"""
        self.publisher = publisher
    
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
                    log.msg("Waiting for messages")
                    message = yield self.queue.get()
                    self.raw_consume(message)
            except queue.Closed, e:
                log.err("Queue has closed: %s" % e)
        read_messages()
        yield None
        returnValue(self)
    
    def raw_consume(self, message):
        self.consume(json.loads(message.content.body))
        self.ack(message)
    
    def consume(self, dictionary):
        log.msg("Received dict: %s" % dictionary)
        self.publisher.publish(dictionary)
    
    def ack(self, message):
        self.channel.basic_ack(message.delivery_tag, True)
    

class Publisher(object):
    exchange_name = "richmond"
    exchange_type = "direct"
    routing_key = "routing_key"
    durable = False
    auto_delete = False
    
    def start(self, channel):
        log.msg("Started the publisher")
        self.channel = channel
    
    def publish(self, data):
        log.msg("Publishing '%s' to exchange '%s' with routing key '%s'" % (
            data, self.exchange_name, self.routing_key))
        message = Content(json.dumps(data))
        message['delivery mode'] = 2 # save to disk
        self.channel.basic_publish(exchange=self.exchange_name, 
                                        content=message, 
                                        routing_key=self.routing_key)
        

class ExampleService(AmqpProtocol):
    
    @inlineCallbacks
    def start_service(self):
        log.msg("Starting the ExampleService")
        self.publisher = yield self.start_publisher(Publisher)
        self.consumer = yield self.start_consumer(Consumer, self.publisher)
    
    def stop_service(self):
        log.msg("Stopping the ExampleService")
    

class AmqpFactory(protocol.ReconnectingClientFactory):
    
    protocol = AmqpProtocol
    
    def __init__(self, specfile, vhost, username, password, protocol=None):
        self.username = username
        self.password = password
        self.vhost = vhost
        self.spec = txamqp.spec.load(specfile)
        self.delegate = TwistedDelegate()
        self.protocol = protocol or self.protocol
    
    def buildProtocol(self, addr):
        protocol = self.protocol(self.delegate, self.vhost, self.spec)
        protocol.factory = self
        self.p = protocol
        self.resetDelay()
        return protocol
    
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed."
        self.p.stop_service()
        protocol.ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
    
    def clientConnectionLost(self, connector, reason):
        print "Client connection lost."
        self.p.stop_service()
        protocol.ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
    

class RichmondService(Service):
    
    def __init__(self, options):
        self.options = options
    
    @inlineCallbacks
    def startService(self):
        log.msg("Starting RichmondService")
        connection = yield self.connect_to_broker(
            self.options['amqp-hostname'],
            self.options['amqp-port'],
            self.options['amqp-specfile'],
            self.options['amqp-vhost'],
            self.options['amqp-username'],
            self.options['amqp-password']
        )
    
    def stopService(self):
        log.msg("Stopping RichmondService")
    
    def connect_to_broker(self, host, port, specfile, vhost, username, password):
        service_class = self.options['service']
        factory = AmqpFactory(specfile, vhost, username, password, service_class)
        reactor.connectTCP(host, port, factory)
    

class RichmondServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "thoughts_plugin"
    description = "Start a Richmond service"
    options = Options
    
    def makeService(self, options):
        return RichmondService(options)

serviceMaker = RichmondServiceMaker()
