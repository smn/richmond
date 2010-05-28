import json
from twisted.internet.defer import inlineCallbacks
from richmond.services.base import RichmondService
from richmond.amqp.base import AMQPConsumer, AMQPPublisher

class Publisher(AMQPPublisher):
    pass

class Consumer(AMQPConsumer):
    def consume_data(self, message):
        self.consume(json.loads(message.content.body))
        self.ack(message)
    

class WorkerService(RichmondService):
    
    consumer_class = Consumer
    publisher_class = Publisher
    
    @inlineCallbacks
    def start(self):
        publisher = yield self.create_publisher(self.publisher_class)
        consumer = yield self.create_consumer(self.consumer_class, publisher)
    
    def stop(self):
        pass
    
