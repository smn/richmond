import logging
from decorator import decorator
from richmond.webapp.api.models import SentSMS, ReceivedSMS

from django.dispatch import Signal
from collections import namedtuple

sms_scheduled = Signal(providing_args=["instance"])
sms_sent = Signal(providing_args=["instance"])
sms_received = Signal(providing_args=["instance"])
sms_receipt = Signal(providing_args=["instance","receipt"])

@decorator
def asynchronous_signal(f, *args, **kwargs):
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
    logging.debug("I should take care of doing callbacks for %s" % received_sms)


def sms_receipt_handler(*args, **kwargs):
    sms_receipt_worker(kwargs['instance'],kwargs['receipt'])

@asynchronous_signal
def sms_receipt_worker(sent_sms, receipt):
    logging.debug("Received receipt for %s -> %s" % (sent_sms.to_msisdn, 
                                                        receipt['status']))