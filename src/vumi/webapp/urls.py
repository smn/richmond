from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

# always load the signals
from richmond.webapp.api.signals import *

urlpatterns = patterns('',
    # Example:
    (r'^api/v1/', include('richmond.webapp.api.urls', namespace="api")),
    (r'^health', include('richmond.webapp.health.urls', namespace="health")),
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
