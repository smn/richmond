import json
# from richmond.workers.base import AMQPWorker
from base import AMQPWorker
from ssmi.client import (SSMI_USSD_TYPE_NEW, SSMI_USSD_TYPE_EXISTING, 
                            SSMI_USSD_TYPE_END, SSMI_USSD_TYPE_TIMEOUT)

class USSDWorker(AMQPWorker):
    
    def reply(self, msisdn, text, reply_type):
        """
        There should be a different worker doing the sending, we publish
        to it's queue here.
        """
        data = {
            "msisdn": msisdn,
            "message": text,
            "ussd_type": reply_type
        }
        raw_data = json.dumps(data)
        self.logger.debug("SEND: %s" % raw_data)
        self.publisher.send(raw_data)
    
    def process_sms(self, *args):
        raise NotImplementedError
    
    def new_ussd_session(self, msisdn, message):
        raise NotImplementedError
    
    def existing_ussd_session(self, msisdn, message):
        raise NotImplementedError
    
    def timed_out_ussd_session(self, msisdn, message):
        raise NotImplementedError
    
    def end_ussd_session(self, msisdn, message):
        raise NotImplementedError
    
    def handle_message(self, raw_data):
        
        self.logger.debug("RECEIVED: %s" % raw_data)
        data = json.loads(raw_data)
        print 'json data:', data
        msisdn = data['msisdn']
        ussd_type = data['ussd_type']
        ussd_phase = data['ussd_phase']
        message = data['message']
        
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
        self.logger.debug('%s timed out, removing client' % msisdn)
    
    def end_ussd_session(self, msisdn, message):
        self.logger.debug('%s ended the session, removing client' % msisdn)
    


if __name__ == '__main__':
    worker = EchoWorker()
    worker.start()
    