import re, yaml, logging
from datetime import datetime, timedelta

from piston.handler import BaseHandler
from piston.utils import rc, throttle, require_mime, validate
from piston.utils import Mimer, FormValidationError

from richmond.webapp.api.models import SentSMS, ReceivedSMS, URLCallback
from richmond.webapp.api import forms
from richmond.webapp.api import signals

from alexandria.loader.base import YAMLLoader
from alexandria.dsl.utils import dump_menu

import pystache

def specify_fields(model, include=[], exclude=[]):
    """
    Silly helper to allow me to specify includes & excludes using the model's
    fields as a base set instead of an empty set.
    """
    include.extend([field.name for field in model._meta.fields
                if field.name not in exclude])
    return exclude, include


# Complete reset, clear defaults - they're hard to debug
Mimer.TYPES = {}
# Specify the default Mime loader for YAML, Piston's YAML loader by default 
# tries to wrap the loaded YAML data in a dict, which for our conversation 
# YAML documents doesn't work.
Mimer.register(yaml.safe_load, ('application/x-yaml',))


class ConversationHandler(BaseHandler):
    allowed_methods = ('POST',)
    
    # @throttle(5, 10*60) # allow 5 times in 10 minutes
    # @require_mime('yaml')
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
            sms.user = request.user
            sms.delivery_status = status
            sms.delivery_at = datetime.utcfromtimestamp(timestamp)
            sms.save()
            
            signals.sms_receipt.send(sender=SentSMS, instance=sms, 
                                        pk=sms.pk, receipt=request.POST.copy())
            
            return rc.CREATED
        except SentSMS.DoesNotExist, e:
            return rc.NOT_FOUND
    


class SendSMSHandler(BaseHandler):
    allowed_methods = ('GET', 'POST',)
    exclude, fields = specify_fields(SentSMS, 
        include=['delivery_status_display'],
        exclude=['user'])
    
    def _send_one(self, **kwargs):
        form = forms.SentSMSForm(kwargs)
        if not form.is_valid():
            raise FormValidationError(form)
        send_sms = form.save()
        logging.debug('Scheduling an SMS to: %s' % kwargs['to_msisdn'])
        signals.sms_scheduled.send(sender=SentSMS, instance=send_sms,
                                    pk=send_sms.pk)
        return send_sms
    
    @throttle(60, 60) # allow for 1 a second
    def create(self, request):
        return [self._send_one(user=request.user.pk, 
                                to_msisdn=msisdn,
                                from_msisdn=request.POST.get('from_msisdn'),
                                message=request.POST.get('message'))
                    for msisdn in request.POST.getlist('to_msisdn')]
    
    @classmethod
    def delivery_status_display(kls, instance):
        return instance.get_delivery_status_display()
    
    @throttle(60, 60)
    def read(self, request, sms_id=None):
        if sms_id:
            return self._read_one(request, sms_id)
        elif 'id' in request.GET:
            return self._read_filtered(request, request.GET.getlist('id'))
        else:
            since = request.GET.get('since', datetime.now() - timedelta(days=30))
            start = request.GET.get('start', 0)
            return self._read_from_point_in_time(request, start, since)
        
    def _read_one(self, request, sms_id):
        return request.user.sentsms_set.get(pk=sms_id)
    
    def _read_filtered(self, request, ids):
        return request.user.sentsms_set.filter(pk__in=map(int, ids))
    
    def _read_from_point_in_time(self, request, start, since):
        qs = request.user.sentsms_set.filter(updated_at__gte=since)
        return qs[start:start+100]
    

class SendTemplateSMSHandler(BaseHandler):
    """
    FIXME: My eyes bleed
    """
    allowed_methods = ('POST',)
    exclude, fields = specify_fields(SentSMS, 
        include=['delivery_status_display'],
        exclude=['user', re.compile(r'^_user_cache')])
    
    def _render_and_send_one(self, to_msisdn, from_msisdn, user_id, \
                                template, context):
        logging.debug('Scheduling an SMS to: %s' % to_msisdn)
        form = forms.SentSMSForm({
            'to_msisdn': to_msisdn,
            'from_msisdn': from_msisdn,
            'message': template.render(context=context),
            'user': user_id
        })
        if not form.is_valid():
            raise FormValidationError(form)
        send_sms = form.save()
        signals.sms_scheduled.send(sender=SentSMS, instance=send_sms, 
                                    pk=send_sms.pk)
        return send_sms
    
    @throttle(60, 60)
    def create(self, request):
        template_string = request.POST.get('template')
        template = pystache.Template(template_string)
        msisdn_list = request.POST.getlist('to_msisdn')
        # not very happy with this template prefix filtering
        context_list = [(key.replace('template_',''), 
                            request.POST.getlist(key)) 
                                for key in request.POST
                                if key.startswith('template_')]
        # check if the nr of entries match
        if not all([len(value) == len(msisdn_list) 
                        for key, value in context_list]):
            response = rc.BAD_REQUEST
            response.content = "Number of to_msisdns and template variables" \
                                " do not match"
            return response
        responses = []
        for msisdn in msisdn_list:
            context = dict([(var_name, var_value_list.pop())
                                for var_name, var_value_list 
                                in context_list])
            send_sms = self._render_and_send_one(
                to_msisdn=msisdn, 
                from_msisdn=request.POST.get('from_msisdn'), 
                user_id=request.user.pk,
                template=template,
                context=context)
            responses.append(send_sms)
        return responses

class ReceiveSMSHandler(BaseHandler):
    allowed_methods = ('POST',)
    model = ReceivedSMS
    exclude = ('user',)
    
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
        request.POST['user'] = request.user
        receive_sms = super(ReceiveSMSHandler, self).create(request)
        signals.sms_received.send(sender=ReceivedSMS, instance=receive_sms, 
                                    pk=receive_sms.pk)
        return receive_sms
    


class URLCallbackHandler(BaseHandler):
    allowed_methods = ('PUT',)
    model = URLCallback
    exclude = ('profile','id')
    
    @throttle(60, 60)
    def update(self, request):
        profile = request.user.get_profile()
        name_field = self.model._meta.get_field('name')
        possible_keys = [key for key, value in name_field.choices]
        return [profile.set_callback(key, request.POST.get(key)) \
                                            for key in possible_keys]