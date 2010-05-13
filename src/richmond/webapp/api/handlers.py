import re
import logging

logging.basicConfig(level=logging.DEBUG)

from piston.handler import BaseHandler
from piston.utils import rc, throttle, require_mime, validate

from richmond.webapp.api.models import SentSMS, ReceivedSMS
from richmond.webapp.api import forms
from datetime import datetime


class ConversationHandler(BaseHandler):
    allowed_methods = ('POST',)
    
    @throttle(5, 10*60) # allow 5 times in 10 minutes
    @require_mime('yaml')
    def create(self, request):
        return rc.CREATED
    

class SMSReceiptHandler(BaseHandler):
    allowed_methods = ('POST',)
    
    @throttle(60, 60) # allow for 1 a second
    @validate(forms.SMSReceiptForm)
    def create(self, request):
        logging.info('Got notified of a delivered SMS to: %s' % request.POST['to'])
        try:
            pk = int(request.POST['cliMsgId'])
            status = int(request.POST['status'])
            timestamp = float(request.POST['timestamp'])
            
            sms = SentSMS.objects.get(id=pk)
            sms.delivery_status = status
            sms.delivery_at = datetime.utcfromtimestamp(timestamp)
            sms.save()
            return rc.CREATED
        except SentSMS.DoesNotExist, e:
            return rc.NOT_FOUND
    


class SendSMSHandler(BaseHandler):
    allowed_methods = ('POST',)
    model = SentSMS
    exclude = ('created_at', 'updated_at', )
    
    @throttle(60, 60) # allow for 1 a second
    @validate(forms.SentSMSForm) # should validate as a valid SMS
    def create(self, request):
        logging.info('Sending an SMS to: %s' % request.POST['to_msisdn'])
        return super(SendSMSHandler, self).create(request)
    

class ReceiveSMSHandler(BaseHandler):
    allowed_methods = ('POST',)
    model = ReceivedSMS
    @throttle(60, 60)
    @validate(forms.ReceivedSMSForm)
    def create(self, request):
        # update the POST to have the `_from` key copied from `from`. 
        # The model has `_from` defined because `from` is a protected python
        # statement
        request.POST['_from'] = request.POST['from']
        del request.POST['from']    # remove because otherwise Django will complain
                                    # about the field not being defined in the model
        logging.info('Receiving an SMS from: %s' % request.POST['_from'])
        return super(ReceiveSMSHandler, self).create(request)
    