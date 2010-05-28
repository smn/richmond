from twisted.python import log
from richmond.services.worker import WorkerService, Publisher, Consumer

class SessionType(object):
    """ussd_type's from SSMI documentation"""
    new = "1"
    existing = "2"
    end = "3"
    timeout = "4"

class WorkerPublisher(Publisher):
    exchange_name = 'richmond'
    routing_key = 'ussd.send'

class WorkerConsumer(Consumer):
    exchange_name = 'richmond'
    exchange_type = 'direct'
    queue_name = 'richmond.ussd.receive'
    routing_key = 'ussd.receive'
    
    def __init__(self, publisher):
        self.publisher = publisher
    
    def reply(self, msisdn, message, ussd_type):
        return self.publisher.send({
            "msisdn": msisdn,
            "message": message,
            "ussd_type": ussd_type
        })
    
    def new_ussd_session(self, msisdn, message):
        raise NotImplementedError
    
    def existing_ussd_session(self, msisdn, message):
        raise NotImplementedError
    
    def timed_out_ussd_session(self, msisdn, message):
        raise NotImplementedError
    
    def end_ussd_session(self, msisdn, message):
        raise NotImplementedError
    
    def consume(self, json):
        log.msg("Received: %s" % json)
        msisdn = json['msisdn']
        ussd_type = json['ussd_type']
        ussd_phase = json['ussd_phase']
        message = json['message']
        
        routes = {
            SessionType.new: self.new_ussd_session,
            SessionType.existing: self.existing_ussd_session,
            SessionType.timeout: self.timed_out_ussd_session,
            SessionType.end: self.end_ussd_session
        }
        
        handler = routes[ussd_type]
        if handler:
            handler(msisdn, message)
        else:
            log.err('FATAL: No handler available for ussd type %s' % ussd_type)
