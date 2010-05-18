from django.dispatch import Signal
from richmond.webapp.api.models import Profile
from richmond.webapp.api.tasks import SendSMSTask, ReceiveSMSTask, DeliveryReportTask

# custom signals for the api
sms_scheduled = Signal(providing_args=['instance', 'pk'])
sms_sent = Signal(providing_args=['instance', 'pk'])
sms_received = Signal(providing_args=['instance', 'pk'])
sms_receipt = Signal(providing_args=['instance', 'pk', 'receipt'])

def sms_scheduled_handler(*args, **kwargs):
    sms_scheduled_worker(kwargs['pk'])

def sms_scheduled_worker(sent_sms_pk):
    """Responsibile for delivering of SMSs"""
    SendSMSTask.delay(pk=sent_sms_pk)

def sms_received_handler(*args, **kwargs):
    sms_received_worker(kwargs['pk'])

def sms_received_worker(received_sms_pk):
    """Responsible for dealing with received SMSs"""
    ReceiveSMSTask.delay(pk=received_sms_pk)

def sms_receipt_handler(*args, **kwargs):
    sms_receipt_worker(kwargs['pk'],kwargs['receipt'])

def sms_receipt_worker(sent_sms_pk, receipt):
    """Responsible for dealing with received SMS delivery receipts"""
    DeliveryReportTask.delay(pk=sent_sms_pk, receipt=receipt)

def create_profile_handler(*args, **kwargs):
    if kwargs['created']:
        create_profile_worker(kwargs['instance'])

def create_profile_worker(user):
    """Automatically create a profile for a newly created user"""
    Profile.objects.create(user=user)
