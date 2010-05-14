import re
import logging
from datetime import datetime

from piston.handler import BaseHandler
from piston.utils import rc, throttle, require_mime, validate

from richmond.webapp.api.models import SentSMS, ReceivedSMS
from richmond.webapp.api import forms
from richmond.webapp.api import signals

from alexandria.loader.base import YAMLLoader
from alexandria.dsl.utils import dump_menu

import pystache

class ConversationHandler(BaseHandler):
    allowed_methods = ('POST',)
    
    @throttle(5, 10*60) # allow 5 times in 10 minutes
    @require_mime('yaml')
    def create(self, request):
        menu = YAMLLoader().load_from_string(request.raw_post_data)
        dump = dump_menu(menu)
        logging.debug("Received a new conversation script with %s items "
                        "but not doing anything with it yet." % len(dump))
        return rc.CREATED
    

class SMSReceiptHandler(BaseHandler):
    allowed_methods = ('POST',)
    
    @throttle(60, 60) # allow for 1 a second
    @validate(forms.SMSReceiptForm)
    def create(self, request):
        logging.debug('Got notified of a delivered SMS to: %s' % request.POST['to'])
        try:
            pk = int(request.POST['cliMsgId'])
            status = int(request.POST['status'])
            timestamp = float(request.POST['timestamp'])
            
            sms = SentSMS.objects.get(id=pk)
            sms.delivery_status = status
            sms.delivery_at = datetime.utcfromtimestamp(timestamp)
            sms.save()
            
            signals.sms_receipt.send(sender=SentSMS, instance=sms, 
                                        receipt=request.POST.copy())
            
            return rc.CREATED
        except SentSMS.DoesNotExist, e:
            return rc.NOT_FOUND
    


class SendSMSHandler(BaseHandler):
    allowed_methods = ('POST',)
    model = SentSMS
    exclude = ('created_at', 'updated_at', )
    
    @throttle(60, 60) # allow for 1 a second
    @validate(forms.SentSMSForm) # should validate as a valid SentSMS
    def create(self, request):
        def send_one(msisdn):
            logging.debug('Scheduling an SMS to: %s' % msisdn)
            data = self.flatten_dict(request.POST)
            data['to_msisdn'] = msisdn
            send_sms = self.model(**data)
            send_sms.save()
            signals.sms_scheduled.send(sender=SentSMS, instance=send_sms)
            return send_sms
        return map(send_one, request.POST.getlist('to_msisdn'))
    


class SendTemplateSMSHandler(BaseHandler):
    """
    FIXME: My eyes bleed
    """
    allowed_methods = ('POST',)
    # model = SentTemplateSMS
    exclude = ('created_at', 'updated_at', )
    
    @throttle(60, 60)
    # @validate(forms.SentTemplateSMSForm)
    def create(self, request):
        template_string = request.POST.get('template')
        template = pystache.Template(template_string)
        
        def send_one(msisdn, context):
            logging.debug('Scheduling an SMS to: %s' % msisdn)
            send_sms = SentSMS(
                to_msisdn = msisdn,
                from_msisdn = request.POST.get('from_msisdn'),
                message = template.render(context=context)
            )
            send_sms.save()
            signals.sms_scheduled.send(sender=SentSMS, instance=send_sms)
            return send_sms
        
        msisdn_list = request.POST.getlist('to_msisdn')
        # not very happy with this template prefix filtering
        context_list = [(key.replace('template_',''), 
                            request.POST.getlist(key)) 
                                for key in request.POST
                                if key.startswith('template_')]
        # check if the nr of entries match
        if not all([len(value) == len(msisdn_list) 
                        for key, value in context_list]):
            return HttpResponse("Number of to_msisdns and template variables"
                                " do not match")
        responses = []
        for msisdn in msisdn_list:
            responses.append(send_one(msisdn, dict(
                (var_name, var_value_list.pop())
                for var_name, var_value_list in context_list
            )))
        return responses

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
        logging.debug('Receiving an SMS from: %s' % request.POST['_from'])
        receive_sms = super(ReceiveSMSHandler, self).create(request)
        signals.sms_received.send(sender=ReceivedSMS, instance=receive_sms)
        return receive_sms
    