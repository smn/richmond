import logging
import pycurl
try:
    # cStringIO is faster
    from cStringIO import StringIO
except ImportError:
    # otherwise this'll do
    from StringIO import StringIO

from decorator import decorator
from richmond.webapp.api.models import (SentSMS, ReceivedSMS, Profile, 
                                        URLCallback)
from richmond.webapp.api.utils import callback

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
    keys_and_values = received_sms.as_list_of_tuples()
    return [callback(urlcallback.url, keys_and_values)
                for callback in 
                URLCallback.objects.filter(name='sms_received')]


def sms_receipt_handler(*args, **kwargs):
    sms_receipt_worker(kwargs['instance'],kwargs['receipt'])

@asynchronous_signal
def sms_receipt_worker(sent_sms, receipt):
    profile = sent_sms.user.get_profile()
    callbacks = profile.urlcallback_set.filter(name='sms_receipt')
    return [callback(urlcallback.url, receipt.entries())
                for callback in callbacks]


def create_profile_handler(*args, **kwargs):
    if kwargs['created']:
        create_profile_worker(kwargs['instance'])

def create_profile_worker(user):
    return Profile.objects.create(user=user)