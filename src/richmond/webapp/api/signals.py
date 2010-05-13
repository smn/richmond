import logging

def post_save_sent_sms_handler(**kwargs):
    post_save_sent_sms(kwargs['instance'])

def post_save_sent_sms(sent_sms):
    logging.debug("I should push %s to the queue" % sent_sms)


def post_save_received_sms_handler(**kwargs):
    post_save_received_sms(kwargs['instance'])

def post_save_received_sms(received_sms):
    logging.debug('I should push %s to the queue' % received_sms)
