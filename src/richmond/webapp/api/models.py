from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
import logging
from clickatell import Clickatell
from utils import model_instance_to_key_values
from django.core import serializers
from richmond.webapp.api.workers import Worker, WorkerManager, expose
from richmond.webapp.api.utils import callback

CLICKATELL_ERROR_CODES = (
    (001, 'Authentication failed'),
    (002, 'Unknown username or password'),
    (003, 'Session ID expired'),
    (004, 'Account frozen'),
    (005, 'Missing session ID'),
    (007, 'IP Lockdown violation'), # You have locked down the API instance to a specific IP address and then sent from an IP address different to the one you set.
    (101, 'Invalid or missing parameters'),
    (102, 'Invalid user data header'),
    (103, 'Unknown API message ID'),
    (104, 'Unknown client message ID'),
    (105, 'Invalid destination address'),
    (106, 'Invalid source address'),
    (107, 'Empty message'),
    (108, 'Invalid or missing API ID'),
    (109, 'Missing message ID'), # This can be either a client message ID or API message ID. For example when using the stop message command.
    (110, 'Error with email message'),
    (111, 'Invalid protocol'),
    (112, 'Invalid message type'),
    (113, 'Maximum message parts'), # The text message component of the message is greater than exceeded the permitted 160 characters (70 Unicode characters). Select concat equal to 1,2,3-N to overcome this by splitting the message across multiple messages.
    (114, 'Cannot route message'), # This implies that the gateway is not currently routing messages to this network prefix. Please email support@clickatell.com with the mobile number in question.
    (115, 'Message expired'),
    (116, 'Invalid Unicode data'),
    (120, 'Invalid delivery time'),
    (121, 'Destination mobile number'), # This number is not allowed to receive messages from us and blocked has been put on our block list.
    (122, 'Destination mobile opted out'),
    (123, 'Invalid Sender ID'), # A sender ID needs to be registered and approved before it can be successfully used in message sending.
    (128, 'Number delisted'), # This error may be returned when a number has been delisted.
    (201, 'Invalid batch ID'),
    (202, 'No batch template'),
    (301, 'No credit left'),
    (302, 'Max allowed credit'),
)

CLICKATELL_MESSAGE_STATUSES = (
    (0, 'Pending locally'), # this is our own status
    (1, 'Message unknown'), # everything above zero is clickatell's status codes
    (2, 'Message queued'),
    (3, 'Delivered to gateway'),
    (4, 'Received by recipient'),
    (5, 'Error with message'),
    (6, 'User cancelled message delivery'),
    (7, 'Error delivering message'),
    (8, 'OK'),
    (9, 'Routing error'),
    (10, 'Message expired'),
    (11, 'Message queued for later delivery'),
    (12, 'Out of credit'),
)


class ClickatellWorker(Worker):
    
    @expose
    def deliver(Worker, pk):
        return ClickatellWorker.sendmsg(SentSMS.objects.get(pk=pk))
    
    @expose
    def sendmsg(Worker, instance):
        message = {
            'to': instance.to_msisdn,
            'from': instance.from_msisdn,
            'text': instance.message,
            'msg_type': 'SMS_TEXT',
            'climsgid': instance.pk
        }
        logging.debug("Clickatell delivery: %s" % message)


class ReceivedSMSWorker(Worker):
    
    @expose
    def callback(Worker, pk):
        received_sms = ReceivedSMS.objects.get(pk=pk)
        keys_and_values = received_sms.as_list_of_tuples()
        profile = received_sms.user.get_profile()
        urlcallback_set = profile.urlcallback_set.filter(name='sms_received')
        resp = [callback(urlcallback.url, keys_and_values)
                    for urlcallback in urlcallback_set]
        return resp
        


class SentSMSReceiptWorker(Worker):
    @expose
    def callback(Worker, pk, receipt):
        sent_sms = SentSMS.objects.get(pk=pk)
        profile = sent_sms.user.get_profile()
        urlcallback_set = profile.urlcallback_set.filter(name='sms_receipt')
        return [callback(urlcallback.url, receipt.entries())
                    for urlcallback in urlcallback_set]
        

# Create your models here.
class SentSMS(models.Model):
    """An Message to be sent through Richmond"""
    user = models.ForeignKey(User)
    to_msisdn = models.CharField(blank=False, max_length=100)
    from_msisdn = models.CharField(blank=False, max_length=100)
    message = models.CharField(blank=False, max_length=160)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, auto_now=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    delivery_status = models.IntegerField(blank=True, null=True, default=0,
                                        choices=CLICKATELL_MESSAGE_STATUSES)
    workers = WorkerManager(
        clickatell = ClickatellWorker(),
        receipt = SentSMSReceiptWorker(),
    )
    
    class Admin:
        list_display = ('',)
        search_fields = ('',)
    
    class Meta:
        ordering = ['-created_at']
        get_latest_by = 'created_at'
    
    def __unicode__(self):
        return u"SentSMS %s -> %s, %s @ %s" % (self.from_msisdn, 
                                            self.to_msisdn, 
                                            self.get_delivery_status_display(), 
                                            self.delivered_at)


class ReceivedSMS(models.Model):
    user = models.ForeignKey(User)
    api_id = models.CharField(max_length=32)
    moMsgId = models.CharField(max_length=32)
    _from = models.CharField(max_length=32)
    to = models.CharField(max_length=32)
    timestamp = models.DateTimeField()
    charset = models.CharField(blank=True, null=True, max_length=32)
    udh = models.CharField(blank=True, null=True, max_length=255)
    text = models.CharField(max_length=160)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, auto_now=True)
    
    workers = WorkerManager(
        received=ReceivedSMSWorker()
    )
    
    class Admin:
        list_display = ('',)
        search_fields = ('',)
    
    class Meta:
        ordering = ['-created_at']
        get_latest_by = ['created_at']
    
    def as_list_of_tuples(self):
        tuple_list = model_instance_to_key_values(self, exclude='_from')
        tuple_list.append(('from', str(self._from)))
        return tuple_list
    
    def __unicode__(self):
        return u"ReceivedSMS %s -> %s @ %s" % (self._from, self.to, 
                                                self.timestamp)


class Profile(models.Model):
    """An API user's profile"""
    user = models.ForeignKey(User, unique=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, auto_now=True)
    
    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return u"Profile"
    
    def set_callback(self, name, url):
        from forms import URLCallbackForm
        kwargs = {
            'name':name, 
            'url': url,
            'profile': self.pk
        }
        try:
            form = URLCallbackForm(kwargs, instance=self.urlcallback_set.get(name=name))
        except URLCallback.DoesNotExist, e:
            form = URLCallbackForm(kwargs)
        
        if form.is_valid():
            return form.save()
        else:
            return False
        

CALLBACK_CHOICES = (
    ('sms_received', 'SMS Received'),
    ('sms_receipt', 'SMS Receipt'),
)

class URLCallback(models.Model):
    """A URL to with to post data for an event"""
    profile = models.ForeignKey(Profile)
    name = models.CharField(blank=True, max_length=255, choices=CALLBACK_CHOICES)
    url = models.URLField(blank=True, verify_exists=False)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, auto_now=True)

from django.db.models.signals import post_save
from richmond.webapp.api import signals
from richmond.webapp.api.signals import sms_scheduled, sms_received, sms_receipt

sms_scheduled.connect(signals.sms_scheduled_handler, sender=SentSMS, weak=False)
sms_received.connect(signals.sms_received_handler, sender=ReceivedSMS, weak=False)
sms_receipt.connect(signals.sms_receipt_handler, sender=SentSMS, weak=False)

post_save.connect(signals.create_profile_handler, sender=User)