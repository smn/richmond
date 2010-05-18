import logging
from celery.task import Task
from celery.task.http import HttpDispatchTask
from richmond.webapp.api.models import SentSMS, ReceivedSMS
from richmond.webapp.api.utils import callback

class SendSMSTask(Task):
    def run(self, pk):
        send_sms = SentSMS.objects.get(pk=pk)
        message = {
            'to': send_sms.to_msisdn,
            'from': send_sms.from_msisdn,
            'text': send_sms.message,
            'msg_type': 'SMS_TEXT',
            'climsgid': send_sms.pk
        }
        logger = self.get_logger(pk=pk)
        logger.debug("Clickatell delivery: %s" % message)
        return message


class ReceiveSMSTask(Task):
    """FIXME: We can probably use the HttpDispatchTask instead of this"""
    def run(self, pk):
        received_sms = ReceivedSMS.objects.get(pk=pk)
        keys_and_values = received_sms.as_tuples()
        print received_sms.as_dict()
        profile = received_sms.user.get_profile()
        urlcallback_set = profile.urlcallback_set.filter(name='sms_received')
        resp = [callback(urlcallback.url, keys_and_values)
                    for urlcallback in urlcallback_set]
        return resp
        


class DeliveryReportTask(Task):
    """FIXME: We can probably use the HttpDispatchTask instead of this"""
    def run(self, pk, receipt):
        sent_sms = SentSMS.objects.get(pk=pk)
        profile = sent_sms.user.get_profile()
        urlcallback_set = profile.urlcallback_set.filter(name='sms_receipt')
        return [callback(urlcallback.url, receipt.entries())
                    for urlcallback in urlcallback_set]
        

