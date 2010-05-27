from richmond.services.base import RichmondService
from richmond.amqp.base import AMQPConsumer, AMQPPublisher

from twisted.python import log
from twisted.python.log import logging

class USSDConsumer(AMQPConsumer):
    exchange_name = "richmond"
    exchange_type = "direct"
    queue_name = "richmond.ussd.receive"
    routing_key = "ussd.receive"
    
    def consume_data(self, message):
        log.msg("Consuming data: %s" % message)
    

class USSDPublisher(AMQPPublisher):
    exchange_name = "richmond"
    routing_key = "ussd.send"

class USSDService(RichmondService):
    
    def start(self):
        deferred = self.start_consumer(USSDConsumer)
        deferred.addCallback(self.consumer_ready)
        deferred.addErrback(lambda f: f.raiseException())
        
        deferred = self.start_publisher(USSDPublisher)
        deferred.addCallback(self.publisher_ready)
        deferred.addErrback(lambda f: f.raiseException())
    
    def consumer_ready(self, consumer):
        log.msg("Consumer ready", consumer)
        self.consumer = consumer
    
    def publisher_ready(self, publisher):
        log.msg("Publisher ready", publisher)
        self.publisher = publisher
    
    def stop(self):
        pass