import re
import logging

logging.basicConfig(level=logging.DEBUG)

from piston.handler import BaseHandler
from piston.utils import rc, throttle, require_mime

class ConversationHandler(BaseHandler):
    allowed_methods = ('POST',)
    
    @throttle(5, 10*60) # allow 5 times in 10 minutes
    @require_mime('yaml')
    def create(self, request):
        return rc.CREATED
    

class SMSReceiptHandler(BaseHandler):
    allowed_methods = ('POST',)
    
    @throttle(60, 60) # allow for 1 a second
    def create(self, request):
        logging.info('Got notified of an delivered SMS: %s' % request.POST)
        return rc.CREATED
    


class SendSMSHandler(BaseHandler):
    allowed_methods = ('POST',)
    
    @throttle(60, 60) # allow for 1 a second
    def create(self, request):
        logging.info("Sending an SMS")
        return rc.CREATED
    

class ReceiveSMSHandler(BaseHandler):
    allowed_methods = ('POST',)
    
    @throttle(60, 60)
    def create(self, request):
        logging.info('Receiving an SMS')
        return rc.CREATED
    