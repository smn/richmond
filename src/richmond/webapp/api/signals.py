import logging
from decorator import decorator
from richmond.webapp.api.models import SentSMS, ReceivedSMS

@decorator
def asynchronous_signal(f, instance):
    logging.debug("I should be calling '%s' asynchronously" % f.__name__)
    return f(instance.pk)

def post_save_sent_sms_handler(**kwargs):
    post_save_sent_sms(kwargs['instance'])

@asynchronous_signal
def post_save_sent_sms(sent_sms_id):
    sent_sms = SentSMS.objects.get(pk=sent_sms_id)
    logging.debug("I should take care of actually sending %s" % sent_sms)


def post_save_received_sms_handler(**kwargs):
    post_save_received_sms(kwargs['instance'])

@asynchronous_signal
def post_save_received_sms(received_sms_id):
    received_sms = ReceivedSMS.objects.get(pk=received_sms_id)
    logging.debug("I should take care of doing callbacks for %s" % received_sms)



