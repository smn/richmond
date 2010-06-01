from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from time import time
from datetime import datetime, timedelta

from richmond.webapp.api.models import *
from richmond.webapp.api.tests.utils import APIClient, mock_sent_messages

class OperaSMSHandlerTestCase(TestCase):
    
    fixtures = ['user_set']
    
    def setUp(self):
        self.client = APIClient()
        self.client.login(username='api', password='password')
        # create the user we need to be authorized
        self.user = User.objects.get(username='api')
    
    def test_sms_receipts(self):
        """
        Receipts received from opera should update the status
        """
        [sms] = mock_sent_messages(self.user, count=1,
                                    transport_name="Opera",
                                    transport_msg_id="001efc31")
        self.assertEquals(sms.transport_status, '')
        
        raw_xml_post = """
        <?xml version="1.0"?>
        <!DOCTYPE receipts>
        <receipts>
          <receipt>
            <msgid>26567958</msgid>
            <reference>001efc31</reference>
            <msisdn>+27123456789</msisdn>
            <status>D</status>
            <timestamp>20080831T15:59:24</timestamp>
            <billed>NO</billed>
          </receipt>
        </receipts>
        """
        
        resp = self.client.post(reverse('api:opera:sms-receipt'), 
                                raw_xml_post.strip(), content_type='text/xml')
        sms = SentSMS.objects.get(pk=sms.pk) # reload
        self.assertEquals(sms.transport_status, 'D')
        self.assertEquals(resp.status_code, 201)
    
    
    def test_sms_sending(self):
        self.assertEquals(SentSMS.objects.count(), 0)
        resp = self.client.post(reverse('api:opera:sms-send'), {
            'to_msisdn': '27123456789',
            'from_msisdn': '27123456789',
            'message': 'yebo',
        })
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(SentSMS.objects.count(), 1)
    
    def test_batch_sms_sending(self):
        self.assertEquals(SentSMS.objects.count(), 0)
        resp = self.client.post(reverse('api:opera:sms-send'), {
            'to_msisdn': ['27123456780','27123456781','27123456782'],
            'from_msisdn': '27123456789',
            'message': 'yebo'
        })
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(SentSMS.objects.count(), 3)
    
    def test_template_sms_sending(self):
        self.assertEquals(SentSMS.objects.count(), 0)
        resp = self.client.post(reverse('api:opera:sms-template-send'), {
            'to_msisdn': ['27123456780','27123456781','27123456782'],
            'template_first_name': ['Name 1', 'Name 2', 'Name 3'],
            'template_last_name': ['Surname 1', 'Surname 2', 'Surname 3'],
            'from_msisdn': '27123456789',
            'template': 'Hi {{first_name}} {{last_name}}',
        })
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(SentSMS.objects.count(), 3)
    
    def test_sms_receiving(self):
        self.assertEquals(ReceivedSMS.objects.count(), 0)
        resp = self.client.post(reverse('api:opera:sms-receive'), {
            'to': '27123456789',
            'from': '27123456789',
            'moMsgId': 'a' * 12,
            'api_id': 'b' * 12,
            'text': 'hello world',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S") # MySQL format
        })
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(ReceivedSMS.objects.count(), 1)
