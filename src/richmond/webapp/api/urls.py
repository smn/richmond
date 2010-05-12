from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication
from richmond.webapp.api.handlers import ConversationHandler

ad = {'authentication': HttpBasicAuthentication(realm="Richmond")}
conversation_resource = Resource(handler=ConversationHandler, **ad)

urlpatterns = patterns('',
    (r'^conversation\.yaml$', conversation_resource, {
        'emitter_format': 'yaml'
    }, 'conversation'),
)
