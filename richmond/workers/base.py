#!/usr/bin/env python
from carrot.connection import BrokerConnection
from carrot.messaging import Consumer, Publisher
import logging
import sys

class AMQPWorker(object):
    
    def __init__(self):
        self.logger = self.create_logger()
        self.connection = self.create_amqp_connection()
        self.consumer = self.create_amqp_consumer(self.connection)
        self.consumer.register_callback(self.receive_message)
        self.publisher = self.create_amqp_publisher(self.connection)
    
    def start(self):
        self.consumer.wait()
    
    def create_amqp_connection(self):
        return BrokerConnection(hostname="localhost", 
                                port=int(5672),
                                userid='richmond',
                                password='richmond',
                                virtual_host='/richmond')
    
    def create_amqp_consumer(self, connection):
        return Consumer(connection=connection, 
                                queue="richmond.receive", 
                                exchange="richmond", 
                                routing_key="ssmi.receive",
                                durable=False)
    
    def create_amqp_publisher(self, connection):
        return Publisher(connection=connection, 
                                queue="richmond.send", 
                                exchange="richmond", 
                                routing_key="ssmi.send",
                                durable=False)
    
    def create_logger(self):
        logger = logging.getLogger("amqp-consumer")
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('[%(name)s] %(asctime)s %(levelname)s %(message)s'))
        logger.addHandler(handler)
        return logger
    
    def receive_message(self, message_data, message):
        self.handle_message(message_data)
        message.ack()
    
    def handle_message(self, message):
        raise NotImplementedError, "must be subclassed"


