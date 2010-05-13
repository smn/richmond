import logging
from decorator import decorator

@decorator
def asynchronous(f, *args, **kwargs):
    logging.debug("I should be calling '%s' asynchronously" % f.__name__)
    return f(*args, **kwargs)

def post_save_sent_sms_handler(**kwargs):
    post_save_sent_sms(kwargs['instance'])

@asynchronous
def post_save_sent_sms(sent_sms):
    logging.debug("I should take care of actually sending %s" % sent_sms)


def post_save_received_sms_handler(**kwargs):
    post_save_received_sms(kwargs['instance'])

@asynchronous
def post_save_received_sms(received_sms):
    logging.debug("I should take care of doing callbacks for %s" % received_sms)



