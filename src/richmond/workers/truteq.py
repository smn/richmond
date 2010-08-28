from twisted.python import log
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import reactor

from richmond.service import Worker, Consumer, Publisher
from ssmi.client import SSMIFactory

class ExampleConsumer(Consumer):
    
    def __init__(self, publisher):
        self.publisher = publisher
    
    def consume_json(self, dictionary):
        log.msg("Consumed JSON %s" % dictionary)
        reactor.callLater(1, self.publisher.publish_json, dictionary)
    

class ExamplePublisher(Publisher):
    
    def publish_json(self, dictionary, **kwargs):
        log.msg("Publishing JSON %s" % dictionary)
        super(ExamplePublisher, self).publish_json(dictionary, **kwargs)
    

class TruTeqWorker(Worker):
    
    @inlineCallbacks
    def startWorker(self):
        log.msg("Starting the TruTeqWorker")
        self.publisher = yield self.start_publisher(TruTeqPublisher)
        self.consumer = yield self.start_consumer(TruTeqConsumer, self.publisher)
        
        host = self.options.pop("truteq_host")
        port = self.options.pop("truteq_port")
        
        # start the transport
        reactor.connectTCP(host, port, SSMIFactory(self.app_register_callback))
    
    def app_register_callback(self, ssmi_client):
        ssmi_client.app_setup(
            username = self.options.pop('truteq_username'),
            password = self.options.pop('truteq_password'),
            ussd_callback = self.ussd_callback
        )
    
    def ussd_callback(self, msisdn, ussd_type, phase, message):
        log.msg("Received ussd from: %s" % msisdn)
        self.publisher.publish_json({
            'msisdn': msisdn,
            'ussd_type': ussd_type,
            'phase': phase
            'message'
        })
    
    def stopWorker(self):
        log.msg("Stopping the TruTeqWorker")
    


