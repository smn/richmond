from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication
from richmond.webapp.api import handlers
from richmond.webapp.api import views

ad = {'authentication': HttpBasicAuthentication(realm="Richmond")}
url_callback_resource = Resource(handler=handlers.URLCallbackHandler, **ad)
conversation_resource = Resource(handler=handlers.ConversationHandler, **ad)

urlpatterns = patterns('',
    (r'^conversation\.yaml$', conversation_resource, {
        'emitter_format': 'yaml'
    }, 'conversation'),
    (r'^account/callbacks.json$', url_callback_resource, {}, 'url-callbacks'),
    (r'^callback\.html$', views.example_sms_callback, {}, 'sms-example-callback'),
)

urlpatterns += patterns('',
    (r'^sms/clickatell/', 
        include('richmond.webapp.api.gateways.clickatell.urls', 
                    namespace='clickatell')),
    (r'^sms/opera/', 
        include('richmond.webapp.api.gateways.opera.urls', 
                    namespace='opera')),
)