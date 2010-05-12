from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication
from richmond.webapp.api import handlers

ad = {'authentication': HttpBasicAuthentication(realm="Richmond")}
conversation_resource = Resource(handler=handlers.ConversationHandler, **ad)
sms_receipt_resource = Resource(handler=handlers.SMSReceiptHandler, **ad)
sms_send_resource = Resource(handler=handlers.SendSMSHandler, **ad)
sms_receive_resource = Resource(handler=handlers.ReceiveSMSHandler, **ad)

urlpatterns = patterns('',
    (r'^conversation\.yaml$', conversation_resource, {
        'emitter_format': 'yaml'
    }, 'conversation'),
    (r'^sms/receipt$', sms_receipt_resource, {}, 'sms-receipt'),
    (r'^sms/send$', sms_send_resource, {}, 'sms-send'),
    (r'^sms/receive$', sms_receive_resource, {}, 'sms-receive'),
)
