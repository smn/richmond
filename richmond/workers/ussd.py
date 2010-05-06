import json
from richmond.workers.base import RichmondWorker
from twisted.python import log
from ssmi import client
from collections import namedtuple

class Session(object):
    new = client.SSMI_USSD_TYPE_NEW
    existing = client.SSMI_USSD_TYPE_EXISTING
    end = client.SSMI_USSD_TYPE_END
    timeout = client.SSMI_USSD_TYPE_TIMEOUT

class USSDWorker(RichmondWorker):
    
    def process_sms(self, *args):
        raise NotImplementedError
    
    def reply(self, msisdn, message, ussd_type):
        return self.publish({
            "msisdn": msisdn,
            "message": message,
            "ussd_type": ussd_type
        })
    
    def new_ussd_session(self, msisdn, message):
        self.reply(msisdn, "so long and thanks for all the fish",
                    Session.end)
    
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
            Session.new: self.new_ussd_session,
            Session.existing: self.existing_ussd_session,
            Session.timeout: self.timed_out_ussd_session,
            Session.end: self.end_ussd_session
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
                            Session.existing)
    
    def existing_ussd_session(self, msisdn, message):
        if message == "0":
            self.reply(msisdn, "quitting, goodbye!", Session.end)
        else:
            self.reply(msisdn, message, Session.existing)
    
    def timed_out_ussd_session(self, msisdn, message):
        log.msg('%s timed out, removing client' % msisdn)
    
    def end_ussd_session(self, msisdn, message):
        log.msg('%s ended the session, removing client' % msisdn)
    

