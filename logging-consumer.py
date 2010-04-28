#!/usr/bin/env python
from carrot.connection import BrokerConnection
from carrot.messaging import Consumer
import logging
import sys

logger = logging.getLogger("amqp-consumer")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

connection = BrokerConnection(hostname="localhost", 
                        port=int(5672),
                        userid='richmond',
                        password='richmond',
                        virtual_host='richmond')

consumer = Consumer(connection=connection, queue="richmond", 
                        exchange="richmond", routing_key="ssmi")

def log_message_and_ack(message_data, message):
    logger.debug(message_data)
    message.ack()

consumer.register_callback(log_message_and_ack)
consumer.wait()
