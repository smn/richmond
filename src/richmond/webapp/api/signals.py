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

def sms_scheduled_handler(*args, **kwargs):
    sms_scheduled_worker(kwargs['pk'])

def sms_scheduled_worker(sent_sms_pk):
    """Responsibile for delivering of SMSs"""
    SentSMS.workers.clickatell.deliver(pk=sent_sms_pk)

def sms_received_handler(*args, **kwargs):
    sms_received_worker(kwargs['pk'])

def sms_received_worker(received_sms_pk):
    """Responsible for dealing with received SMSs"""
    ReceivedSMS.workers.received.callback(pk=received_sms_pk)

def sms_receipt_handler(*args, **kwargs):
    sms_receipt_worker(kwargs['pk'],kwargs['receipt'])

def sms_receipt_worker(sent_sms_pk, receipt):
    """Responsible for dealing with received SMS delivery receipts"""
    SentSMS.workers.receipt.callback(pk=sent_sms_pk, receipt=receipt)

def create_profile_handler(*args, **kwargs):
    if kwargs['created']:
        create_profile_worker(kwargs['instance'])

def create_profile_worker(user):
    """Automatically create a profile for a newly created user"""
    Profile.objects.create(user=user)
