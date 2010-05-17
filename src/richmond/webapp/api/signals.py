import logging
from decorator import decorator
from richmond.webapp.api.models import (SentSMS, ReceivedSMS, Profile, 
                                        URLCallback)
from richmond.webapp.api.utils import callback

from django.dispatch import Signal
from django.core import serializers
from django.conf import settings

# custom signals for the api
sms_scheduled = Signal(providing_args=['instance', 'pk'])
sms_sent = Signal(providing_args=['instance', 'pk'])
sms_received = Signal(providing_args=['instance', 'pk'])
sms_receipt = Signal(providing_args=['instance', 'pk', 'receipt'])

@decorator
def asynchronous_signal(f, *args, **kwargs):
    """
    Make the signal asynchronous, allow for background processing via a queue
    """
    logging.debug("I should be calling '%s' asynchronously" % f.__name__)
    # Still need to handle the serialization
    return f(*args, **kwargs)

def sms_scheduled_handler(*args, **kwargs):
    sms_scheduled_worker(kwargs['pk'])

@asynchronous_signal
def sms_scheduled_worker(sent_sms_pk):
    """Responsibile for delivering of SMSs"""
    SentSMS.clickatell.deliver(pk=sent_sms_pk)


def sms_received_handler(*args, **kwargs):
    sms_received_worker(kwargs['pk'])

@asynchronous_signal
def sms_received_worker(received_sms_pk):
    """Responsible for dealing with received SMSs"""
    received_sms = ReceivedSMS.objects.get(pk=received_sms_pk)
    keys_and_values = received_sms.as_list_of_tuples()
    profile = received_sms.user.get_profile()
    urlcallback_set = profile.urlcallback_set.filter(name='sms_received')
    resp = [callback(urlcallback.url, keys_and_values)
                for urlcallback in urlcallback_set]
    return resp


def sms_receipt_handler(*args, **kwargs):
    sms_receipt_worker(kwargs['pk'],kwargs['receipt'])

@asynchronous_signal
def sms_receipt_worker(sent_sms_pk, receipt):
    """Responsible for dealing with received SMS delivery receipts"""
    sent_sms = SentSMS.objects.get(pk=sent_sms_pk)
    profile = sent_sms.user.get_profile()
    urlcallback_set = profile.urlcallback_set.filter(name='sms_receipt')
    return [callback(urlcallback.url, receipt.entries())
                for urlcallback in urlcallback_set]


def create_profile_handler(*args, **kwargs):
    if kwargs['created']:
        create_profile_worker(kwargs['instance'])

def create_profile_worker(user):
    """Automatically create a profile for a newly created user"""
    return Profile.objects.create(user=user)