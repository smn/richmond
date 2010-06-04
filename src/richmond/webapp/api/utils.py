import pycurl
import logging
from decorator import decorator
from django.http import HttpResponse
try:
    # cStringIO is faster
    from cStringIO import StringIO
except ImportError:
    # otherwise this'll do
    from StringIO import StringIO

def model_to_tuples(instance, exclude=[]):
    """
    Somewhat lame function to convert a model instance's fields & values to
    string values, ready for posting over HTTP
    
    >>> from django.db import models
    >>> class TestModel(models.Model):
    ...     __module__ = 'richmond.webapp.api.models'
    ...     integer = models.IntegerField(blank=True, null=True, default=1)
    ...     _float = models.FloatField(default=1.0)
    ...     created_at = models.DateTimeField(blank=True, auto_now_add=True)
    ...     updated_at = models.DateTimeField(blank=True, auto_now=True)
    ... 
    >>> model_to_tuples(instance=TestModel())
    (('id', 'None'), ('integer', '1'), ('_float', '1.0'), ('created_at', ''), ('updated_at', ''))
    >>> 
    
    """
    fields = [field for field in instance._meta.fields 
                if field.name not in exclude]
    resp = [(str(field.name), str(field.value_to_string(instance))) 
                for field in fields]
    return tuple(resp)

def model_to_dict(instance, exclude=[]):
    return dict(model_to_tuples(instance, exclude))

def callback(url, list_of_tuples):
    """
    HTTP POST a list of key value tuples to the given URL and 
    return the response
    """
    data = StringIO()
    ch = pycurl.Curl()
    ch.setopt(pycurl.URL, str(url))
    ch.setopt(pycurl.VERBOSE, 0)
    ch.setopt(pycurl.SSLVERSION, 3)
    ch.setopt(pycurl.SSL_VERIFYPEER, 1)
    ch.setopt(pycurl.SSL_VERIFYHOST, 2)
    ch.setopt(pycurl.HTTPHEADER, [
            "User-Agent: Richmond Callback Client"
            "Accept:"
        ])
    ch.setopt(pycurl.WRITEFUNCTION, data.write)
    ch.setopt(pycurl.HTTPPOST, list_of_tuples)
    ch.setopt(pycurl.FOLLOWLOCATION, 1)
    
    try:
        result = ch.perform()
        resp = data.getvalue()
        logging.debug("Posting to %s which returned %s" % (url, resp))
        return (url, resp)
    except pycurl.error, e:
        logging.debug("Posting to %s resulted in error: %s" % (url, e))
        return (url, e)


def require_content_type(*content_types):
    """
    Decorator requiring a certain content-type. Like piston's require_mime but
    then without the silly hardcoded rewrite dict.
    """
    @decorator
    def wrap(f, self, request, *args, **kwargs):
        c_type_string = request.META.get('CONTENT_TYPE', None)
        if c_type_string:
            c_type_parts = c_type_string.split(";", 1)
            c_type = c_type_parts[0].strip()
            if not c_type in content_types:
                return HttpResponse(
                    "Bad Request, only '%s' allowed" % "', '".join(content_types), 
                    content_type='text/plain', 
                    status="400")
        return f(self, request, *args, **kwargs)
    return wrap
