from django.conf.urls.defaults import *
from django.http import HttpResponse

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

def debug(request, *args, **kwargs):
    print request.POST
    print request.META
    return HttpResponse("ok")

urlpatterns = patterns('',
    # Example:
    (r'^api/v1/', include('richmond.webapp.api.urls', namespace="api")),
    (r'^debug/(.*)$', debug),
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)
