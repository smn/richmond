import pycurl
import logging
from decorator import decorator
try:
    # cStringIO is faster
    from cStringIO import StringIO
except ImportError:
    # otherwise this'll do
    from StringIO import StringIO

def model_instance_to_key_values(instance, exclude=[]):
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
    >>> model_instance_to_key_values(instance=TestModel())
    [('id', 'None'), ('integer', '1'), ('_float', '1.0'), ('created_at', ''), ('updated_at', '')]
    >>> 
    
    """
    fields = [field for field in instance._meta.fields 
                if field.name not in exclude]
    resp = [(str(field.name), str(field.value_to_string(instance))) 
                for field in fields]
    return resp

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
