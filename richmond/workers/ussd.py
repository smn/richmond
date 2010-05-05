import json
from richmond.workers.base import RichmondWorker
from twisted.python import log
from ssmi.client import (SSMI_USSD_TYPE_NEW, SSMI_USSD_TYPE_EXISTING, 
                            SSMI_USSD_TYPE_END, SSMI_USSD_TYPE_TIMEOUT)

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
                    SSMI_USSD_TYPE_END)
    
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
            SSMI_USSD_TYPE_NEW: self.new_ussd_session,
            SSMI_USSD_TYPE_EXISTING: self.existing_ussd_session,
            SSMI_USSD_TYPE_TIMEOUT: self.timed_out_ussd_session,
            SSMI_USSD_TYPE_END: self.end_ussd_session
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
                            SSMI_USSD_TYPE_EXISTING)
    
    def existing_ussd_session(self, msisdn, message):
        if message == "0":
            self.reply(msisdn, "quitting, goodbye!", SSMI_USSD_TYPE_END)
        else:
            self.reply(msisdn, message, SSMI_USSD_TYPE_EXISTING)
    
    def timed_out_ussd_session(self, msisdn, message):
        log.msg('%s timed out, removing client' % msisdn)
    
    def end_ussd_session(self, msisdn, message):
        log.msg('%s ended the session, removing client' % msisdn)
    

