import logging
from django.conf import settings
from celery.task import Task
from celery.task.http import HttpDispatchTask
from richmond.webapp.api.models import SentSMS, ReceivedSMS
from richmond.webapp.api.utils import callback

from clickatell.api import Clickatell
from clickatell.response import OKResponse, ERRResponse

class SendSMSTask(Task):
    routing_key = 'richmond.webapp.sms.send'
    
    def run(self, pk):
        send_sms = SentSMS.objects.get(pk=pk)
        logger = self.get_logger(pk=pk)
        clickatell = Clickatell(settings.CLICKATELL_USERNAME,
                                settings.CLICKATELL_PASSWORD, 
                                settings.CLICKATELL_API_ID,
                                sendmsg_defaults=settings.CLICKATELL_DEFAULTS['sendmsg'])
        [resp] = clickatell.sendmsg(recipients=[send_sms.to_msisdn],
                            sender=send_sms.from_msisdn,
                            text=send_sms.message,
                            climsgid=send_sms.pk)
        logger.debug("Clickatell delivery: %s" % resp)
        if isinstance(resp, OKResponse):
            return resp
        else:
            logger.debug("Retrying...")
            self.retry(args=[pk], kwargs={})


class ReceiveSMSTask(Task):
    routing_key = 'richmond.webapp.sms.receive'
    
    """FIXME: We can probably use the HttpDispatchTask instead of this"""
    def run(self, pk):
        received_sms = ReceivedSMS.objects.get(pk=pk)
        keys_and_values = received_sms.as_tuples()
        profile = received_sms.user.get_profile()
        urlcallback_set = profile.urlcallback_set.filter(name='sms_received')
        resp = [callback(urlcallback.url, keys_and_values)
                    for urlcallback in urlcallback_set]
        return resp
        


class DeliveryReportTask(Task):
    routing_key = 'richmond.webapp.sms.receipt'
    
    """FIXME: We can probably use the HttpDispatchTask instead of this"""
    def run(self, pk, receipt):
        sent_sms = SentSMS.objects.get(pk=pk)
        profile = sent_sms.user.get_profile()
        urlcallback_set = profile.urlcallback_set.filter(name='sms_receipt')
        return [callback(urlcallback.url, receipt.entries())
                    for urlcallback in urlcallback_set]
        

