from django.conf.urls.defaults import *
from richmond.webapp.api import views

urlpatterns = patterns('',
    (r'^conversation\.yaml$', views.conversation, {'format': 'yaml'}, 'conversation'),
)
