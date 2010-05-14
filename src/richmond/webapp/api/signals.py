import logging
import pycurl
try:
    # cStringIO is faster
    from cStringIO import StringIO
except ImportError:
    # otherwise this'll do
    from StringIO import StringIO

from decorator import decorator
from richmond.webapp.api.models import SentSMS, ReceivedSMS, Profile, URLCallback

from django.dispatch import Signal
from django.core import serializers
from django.conf import settings

# custom signals for the api
sms_scheduled = Signal(providing_args=["instance"])
sms_sent = Signal(providing_args=["instance"])
sms_received = Signal(providing_args=["instance"])
sms_receipt = Signal(providing_args=["instance","receipt"])

@decorator
def asynchronous_signal(f, *args, **kwargs):
    """
    Make the signal asynchronous, allow for background processing via a queue
    """
    logging.debug("I should be calling '%s' asynchronously" % f.__name__)
    # i'll handle the serialization at worker level I think
    return f(*args, **kwargs)

def sms_scheduled_handler(*args, **kwargs):
    sms_scheduled_worker(kwargs['instance'])

@asynchronous_signal
def sms_scheduled_worker(sent_sms):
    SentSMS.clickatell.deliver(sent_sms.pk)


def sms_received_handler(*args, **kwargs):
    sms_received_worker(kwargs['instance'])

@asynchronous_signal
def sms_received_worker(received_sms):
    """FIXME: This needs to be smaller"""
    def callback(url, list_of_tuples):
        data = StringIO()
        ch = pycurl.Curl()
        ch.setopt(pycurl.URL, url)
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
            logging.debug("Posted %s to %s which returned %s" % (post, url, resp))
            return (url, resp)
        except pycurl.error, v:
            logging.error("Posting %s to %s resulted in error: %s" % (post, url, v))
            return (url, v)
        
    keys_and_values = received_sms.as_list_of_tuples()
    return [callback(urlcallback.url, keys_and_values)
                for callback in 
                URLCallback.objects.filter(name='sms_received')]


def sms_receipt_handler(*args, **kwargs):
    sms_receipt_worker(kwargs['instance'],kwargs['receipt'])

@asynchronous_signal
def sms_receipt_worker(sent_sms, receipt):
    logging.debug("Received receipt for %s -> %s" % (sent_sms.to_msisdn, 
                                                        receipt['status']))


def create_profile_handler(*args, **kwargs):
    if kwargs['created']:
        create_profile_worker(kwargs['instance'])

def create_profile_worker(user):
    return Profile.objects.create(user=user)