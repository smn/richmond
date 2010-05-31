from twisted.python import log
from twisted.python.log import logging
from richmond.amqp.base import AMQPConsumer
import json

class RichmondWorker(AMQPConsumer):
    publisher = None
    def set_publisher(self, publisher):
        log.msg("RichmondWorker will publish to: %s" % publisher)
        self.publisher = publisher
    
    def publish(self, data):
        self.publisher.send(data)
    
    def consume(self, data):
        log.msg("Please override consume as I'm not doing anything yet.")
        log.msg("Ignore message: %s" % data)
    
    def ack(self, message):
        self.channel.basic_ack(message.delivery_tag, True)
    
    def start(self):
        if self.publisher:
            super(RichmondWorker, self).start()
        else:
            raise RuntimeException, """This consumer cannot start without having been assigned a publisher first."""
    
    def consume_data(self, message):
        self.consume(json.loads(message.content.body))
        self.ack(message)
            


