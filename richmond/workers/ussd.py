import json
from richmond.workers.base import RichmondWorker
from twisted.python import log
from ssmi import client
from collections import namedtuple

class SessionType(object):
    new = client.SSMI_USSD_TYPE_NEW
    existing = client.SSMI_USSD_TYPE_EXISTING
    end = client.SSMI_USSD_TYPE_END
    timeout = client.SSMI_USSD_TYPE_TIMEOUT

class USSDWorker(RichmondWorker):
    
    def reply(self, msisdn, message, ussd_type):
        return self.publish({
            "msisdn": msisdn,
            "message": message,
            "ussd_type": ussd_type
        })
    
    def new_ussd_session(self, msisdn, message):
        self.reply(msisdn, "so long and thanks for all the fish",
                    SessionType.end)
    
    def existing_ussd_session(self, msisdn, message):
        raise NotImplementedError
    
    def timed_out_ussd_session(self, msisdn, message):
        raise NotImplementedError
    
    def end_ussd_session(self, msisdn, message):
        raise NotImplementedError
    
    def consume(self, json):
        log.msg("RECEIVED: %s" % json)
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
        
    

class EchoWorker(USSDWorker):
    
    def new_ussd_session(self, msisdn, message):
        self.reply(msisdn, "Hello, this is an echo service for testing. "
                            "Reply with whatever. Reply '0' to end session.", 
                            SessionType.existing)
    
    def existing_ussd_session(self, msisdn, message):
        if message == "0":
            self.reply(msisdn, "quitting, goodbye!", SessionType.end)
        else:
            self.reply(msisdn, message, SessionType.existing)
    
    def timed_out_ussd_session(self, msisdn, message):
        log.msg('%s timed out, removing client' % msisdn)
    
    def end_ussd_session(self, msisdn, message):
        log.msg('%s ended the session, removing client' % msisdn)
    

