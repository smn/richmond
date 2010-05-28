from richmond.services.base import RichmondService
from richmond.services.truteq import ssmi_service
from richmond.amqp.base import AMQPConsumer, AMQPPublisher
from richmond.workers.ussd import SessionType

from twisted.python import log
from twisted.python.log import logging

import json


class USSDHandler(ssmi_service.SSMICallback):
    
    def __init__(self, ssmi_client, publisher, consumer):
        self.ssmi_client = ssmi_client
        self.publisher = publisher
        self.consumer = consumer
        # tell consumer to use our consume_callback
        self.consumer.consume_callback = self.consume
    
    def consume(self, data):
        """
        We've monkey patched the consumer's `consume` method to point to this
        one intead. All incoming data are messages that need to be sent
        to TruTeq over USSD. Use `ssmi_client.send_ussd` to do that.
        """
        self.ssmi_client.send_ussd(
            str(data['msisdn']),    # str everything because the SSMIClient
            str(data['message']),   # isn't happy with Unicode
            str(data['ussd_type']))
        
    
    def ussd_callback(self, msisdn, ussd_type, ussd_phase, message):
        """
        Called by SSMICallback, override for our own custom behaviour. In
        our case we want it to publish to the queue via our publisher.
        """
        self.publisher.send({
            'msisdn': msisdn,
            'ussd_type': ussd_type,
            'ussd_phase': ussd_phase,
            'message': message,
        })
    

class USSDConsumer(AMQPConsumer):
    """
    Consumer for receiving all responses from workers published as json
    to the exchange richmond with the routing key 'ussd.send'.
    """
    exchange_name = "richmond"
    exchange_type = "direct"
    queue_name = "richmond.ussd.send"
    routing_key = "ussd.send"
    consume_callback = None
    
    def consume_data(self, message):
        """
        AMQPConsumer calls consume_data when new messages arrive over
        the queue. We override it for our custom behaviour
        """
        data = json.loads(message.content.body)
        if self.consume_callback:
            self.consume_callback(data)
            self.ack(message)
        else:
            log.msg('No consume_callback specified, cannot do anything '\
                        'with %s' % data)
        
    

class USSDPublisher(AMQPPublisher):
    """
    Publisher for publishing all incoming traffic over SSMI to the exchange
    richmond with the routing_key 'ussd.receive'.
    """
    exchange_name = "richmond"
    routing_key = "ussd.receive"


class USSDService(RichmondService):
    """
    For a USSD service we need both a publisher and a consumer. Individual
    workers cannot publish straight back to USSD because we only have one
    login for the service and SSMI doesn't allow multiple sessions for a
    single login.
    
    The app works like so:
    
        1. Phone connects to TruTeq
        2. TruTeq sends message over SSMI protocol to us
        3. Service publishes message as JSON with routing key 'ussd.receive'
        4. Workers listen to 'ussd.receive' on queue 'richmond.ussd.receive'
        5. Workers publish JSON response with routing key 'ussd.send'
        6. Service listens to 'ussd.send' on queue 'richmond.ussd.send'
        7. Services sends message over SSMI protocol to TruTeq.
    
    """
    def start(self):
        """
        Start is called by RichmondService when this it has connected
        to the AMQP backend and is ready for pub/sub madness
        """
        self.start_consumer()
    
    def start_consumer(self):
        """
        Start a consumer for this service, when it's ready, return the result
        to consumer_ready
        """
        d = self.create_consumer(USSDConsumer)
        d.addCallback(self.consumer_ready)
        d.addErrback(lambda f: f.raiseException())
    
    def consumer_ready(self, consumer):
        """
        Consumer is ready, store it and start the publisher
        """
        log.msg("Consumer ready")
        self.consumer = consumer
        self.start_publisher()
    
    def start_publisher(self):
        """
        Start a publisher for this service, when it's ready, return the result
        to publisher_ready
        """
        log.msg("Starting publisher")
        d = self.create_publisher(USSDPublisher)
        d.addCallback(self.publisher_ready)
        d.addErrback(lambda f: f.raiseException())
    
    def publisher_ready(self, publisher):
        """
        Publisher is ready, store it and start the SSMI service
        """
        log.msg("Publisher ready")
        self.publisher = publisher
        self.start_ssmi_service()
    
    def start_ssmi_service(self):
        """
        Called when both the consumer & publisher are ready. When we connect
        succesfully to the SSMI service then return the SSMIClient to 
        ssmi_service_ready
        """
        self.ssmi_srv = ssmi_service.SSMIService('praekelttest2', 
                                            'LIUMIOYTM',
                                            'sms.truteq.com', 
                                            50008)
        self.ssmi_srv.onConnectionMade.addCallback(self.ssmi_service_ready)
        self.ssmi_srv.onConnectionMade.addErrback(lambda f: f.raiseException())
        self.ssmi_srv.setServiceParent(self) # RichmondService is a MultiService,
                                        # it tracks the start & stop of
                                        # multiple services, calling setServiceParent
                                        # registers this service for monitoring
                                        
    def ssmi_service_ready(self, ssmi_client):
        """
        Start the callback instance, responsible for dealing with whatever
        arrives over SSMI. The SSMIClient is our only means of communicating
        with TruTeq, pass it along with the publisher and the consumer along
        to the USSDHandler so that it can both receive and reply.
        """
        ussd_handler = USSDHandler(ssmi_client, self.publisher, self.consumer)
        ssmi_client.set_handler(ussd_handler)
        return ssmi_client
    
    def stop(self):
        """Called when this service is stopping"""
        pass