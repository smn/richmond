from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication
from richmond.webapp.api import handlers
from richmond.webapp.api import views

ad = {'authentication': HttpBasicAuthentication(realm="Richmond")}

url_callback_resource = Resource(handler=handlers.URLCallbackHandler, **ad)

conversation_resource = Resource(handler=handlers.ConversationHandler, **ad)

sms_receipt_resource = Resource(handler=handlers.SMSReceiptHandler, **ad)
sms_send_resource = Resource(handler=handlers.SendSMSHandler, **ad)
sms_template_send_resource = Resource(handler=handlers.SendTemplateSMSHandler, **ad)
sms_receive_resource = Resource(handler=handlers.ReceiveSMSHandler, **ad)

urlpatterns = patterns('',
    (r'^conversation\.yaml$', conversation_resource, {
        'emitter_format': 'yaml'
    }, 'conversation'),
    (r'^account/callbacks.json$', url_callback_resource, {}, 'url-callbacks'),
    (r'^sms/receipt\.json$', sms_receipt_resource, {}, 'sms-receipt'),
    (r'^sms/send\.json$', sms_send_resource, {}, 'sms-send'),
    (r'^sms/status\.json$', sms_send_resource, {}, 'sms-status-list'),
    (r'^sms/status/(?P<sms_id>\d+)\.json$', sms_send_resource, {}, 'sms-status'),
    (r'^sms/template_send\.json$', sms_template_send_resource, {}, 'sms-template-send'),
    (r'^sms/receive\.json$', sms_receive_resource, {}, 'sms-receive'),
    (r'^callback\.html$', views.example_sms_callback, {}, 'sms-example-callback'),
)

from celery.decorators import task

@task
def add(x, y):
    return x + y
