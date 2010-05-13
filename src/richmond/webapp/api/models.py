from django.db import models
from datetime import datetime

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

# Create your models here.
class SentSMS(models.Model):
    """An Message to be sent through Richmond"""
    to_msisdn = models.CharField(blank=False, max_length=100)
    from_msisdn = models.CharField(blank=False, max_length=100)
    message = models.CharField(blank=False, max_length=160)
    created_at = models.DateTimeField(blank=True, default=datetime.now)
    updated_at = models.DateTimeField(blank=True, default=datetime.now)
    delivered_at = models.DateTimeField(blank=True, default=datetime.now)
    delivery_status = models.IntegerField(blank=True, null=True, default=0,
                                        choices=CLICKATELL_MESSAGE_STATUSES)
    
    class Admin:
        list_display = ('',)
        search_fields = ('',)
    
    def __unicode__(self):
        return u"SentSMS %s -> %s, %s @ %s" % (self.from_msisdn, 
                                            self.to_msisdn, 
                                            self.get_delivery_status_display(), 
                                            self.delivered_at)

class ReceivedSMS(models.Model):
    api_id = models.CharField(max_length=32)
    moMsgId = models.CharField(max_length=32)
    _from = models.CharField(max_length=32)
    to = models.CharField(max_length=32)
    timestamp = models.DateTimeField()
    charset = models.CharField(blank=True, null=True, max_length=32)
    udh = models.CharField(blank=True, null=True, max_length=255)
    text = models.CharField(max_length=160)
    
    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return u"ReceivedSMS %s -> %s @ %s" % (self._from, self.to, 
                                                self.timestamp)

from django.db.models.signals import post_save
from richmond.webapp.api import signals

post_save.connect(signals.post_save_sent_sms_handler, sender=SentSMS, weak=False)
post_save.connect(signals.post_save_received_sms_handler, sender=ReceivedSMS, weak=False)
