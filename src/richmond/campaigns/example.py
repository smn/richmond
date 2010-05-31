from richmond.workers.ussd import USSDWorker, SessionType
from twisted.python import log

class FooBarWorker(USSDWorker):
    
    def new_ussd_session(self, msisdn, message):
        """Respond to new sessions"""
        self.reply(msisdn, "foo?", SessionType.existing)
        
    def existing_ussd_session(self, msisdn, message):
        """Respond to returning sessions"""
        if message == "bar" or message == "0": # sorry android is silly
            # replying with type `SessionType.end` ends the session
            self.reply(msisdn, "Clever. Bye!", SessionType.end)
        else:
            # replying with type `SessionType.existing` keeps the session
            # open and prompts the user for input
            self.reply(msisdn, "Say bar ...", SessionType.existing)
    
    def timed_out_ussd_session(self, msisdn, message):
        """These timed out unfortunately"""
        log.msg("%s timed out" % msisdn)
    
    def end_ussd_session(self, msisdn, message):
        """These ended the session themselves"""
        log.msg("%s ended session" % msisdn)
    
    