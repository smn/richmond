from twisted.python import log
from twisted.python.log import logging
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import reactor

from richmond.service import Worker, Consumer, Publisher
from richmond.workers.truteq.util import RichmondSSMIFactory, SessionType

def ussd_code_to_routing_key(ussd_code):
    # convert *120*663*79# to s120s663s79h since
    # * and # are wildcards for AMQP based routing
    ussd_code = ussd_code.replace("*","s")
    ussd_code = ussd_code.replace("#","h")
    return ussd_code


class TruTeqConsumer(Consumer):
    exchange_name = "richmond.ussd"
    exchange_type = "topic"
    durable = False
    queue_name = "ussd.truteq"
    routing_key = "ussd.truteq.#"
    
    def __init__(self, send_callback):
        self.send = send_callback
    
    def consume_json(self, dictionary):
        log.msg("Consumed JSON %s" % dictionary)
        self.send(**dictionary)
    

class TruTeqPublisher(Publisher):
    exchange_name = "richmond.ussd"
    exchange_type = "topic"             # -> route based on pattern matching
    routing_key = 'ussd.fallback'       # -> overriden in publish method
    durable = False                     # -> not created at boot
    auto_delete = False                 # -> auto delete if no consumers bound
    delivery_mode = 2                   # -> do not save to disk
    
    def publish_json(self, dictionary, **kwargs):
        log.msg("Publishing JSON %s with extra args: %s" % (dictionary, kwargs))
        super(TruTeqPublisher, self).publish_json(dictionary, **kwargs)
    

class USSDTransport(Worker):
    
    def startWorker(self):
        log.msg("Starting the USSDTransport")
        
        username = self.config.pop('username')
        password = self.config.pop('password')
        host = self.config.pop("host")
        port = self.config.pop("port")
        
        # this needs to be done more intelligently, it stores which
        # MSISDN dialed into which ussd code
        self.storage = {}
        
        # start the USSD transport
        factory = RichmondSSMIFactory(username, password)
        factory.onConnectionMade.addCallback(self.ssmi_connected)
        reactor.connectTCP(host, port, factory)
    
    @inlineCallbacks
    def ssmi_connected(self, client):
        log.msg("SSMI Connected, adding handlers")
        self.ssmi_client = client
        self.ssmi_client.set_handler(self)
        self.publisher = yield self.start_publisher(TruTeqPublisher)
        self.consumer = yield self.start_consumer(TruTeqConsumer, self.send_ussd)
    
    def ussd_callback(self, msisdn, ussd_type, phase, message):
        print "Received USSD, from: %s, message: %s" % (msisdn, message)
        
        # FIXME
        if ussd_type == SessionType.NEW:
            # cache
            ussd_code = self.storage[msisdn] = message
            options = {
                'routing_key': ussd_code_to_routing_key('ussd.%s' % ussd_code)
            }
        elif ussd_type in [SessionType.END, SessionType.TIMEOUT]:
            # clear cache
            if msisdn in self.storage:
                del self.storage[msisdn]
            options = {}
        else:
            # read cache
            ussd_code = self.storage.get(msisdn)
            options = {
                'routing_key': ussd_code_to_routing_key('ussd.%s' % ussd_code)
            }
        
        self.publisher.publish_json({
            'msisdn': msisdn, 
            'ussd_type': ussd_type, 
            'phase': phase, 
            'message': message
        }, **options)
    
    def send_ussd(self, msisdn, ussd_type, message):
        print "Sending USSD, to: %s, message: %s" % (msisdn, message)
        self.ssmi_client.send_ussd(str(msisdn), str(message), str(ussd_type))
    
    def sms_callback(self, *args, **kwargs):
        print "Got SMS:", args, kwargs
    
    def errback(self, *args, **kwargs):
        print "Got Error: ", args, kwargs
    
    def stopWorker(self):
        log.msg("Stopping the USSDTransport")
    


