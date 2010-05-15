import pycurl
import logging
try:
    # cStringIO is faster
    from cStringIO import StringIO
except ImportError:
    # otherwise this'll do
    from StringIO import StringIO

def model_instance_to_key_values(instance, exclude=[]):
    field_names = [field.name for field in instance._meta.fields]
    key_values = [(key, getattr(instance, key)) for
                    key in field_names
                    if key not in exclude]
    return [(str(key), str(value))
                for key,value in key_values
                if value]

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
