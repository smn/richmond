from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
import base64
from time import time
from datetime import datetime, timedelta

from richmond.webapp.api.models import *

import logging
logging.basicConfig(level=logging.DEBUG)

class APIClient(Client):
    
    username = None
    password = None
    
    def request(self, **request):
        if ('HTTP_AUTHORIZATION' not in request) \
            and (self.username and self.password):
            b64 = base64.encodestring('%s:%s' % (
                self.username, 
                self.password
            )).strip()
            request.update({'HTTP_AUTHORIZATION': 'Basic %s' % b64})
        return super(APIClient, self).request(**request)
    
    def login(self, username, password):
        """Overridge the cookie based login of Client, 
        we're using HTTP Basic Auth instead."""
        self.username = username
        self.password = password

def mock_sent_messages(user, count=1,to_msisdn='27123456789', 
                        from_msisdn='27123456789', message='testing api', 
                        **kwargs):
    return [SentSMS.objects.create(to_msisdn=to_msisdn, 
                                    from_msisdn=from_msisdn, 
                                    message=message,
                                    user=user, 
                                    **kwargs) for i in range(0,count)]



class ApiHandlerTestCase(TestCase):
    
    fixtures = ['user_set']
    
    def setUp(self):
        self.client = APIClient()
        self.client.login(username='api', password='password')
        # create the user we need to be authorized
        self.user = User.objects.get(username='api')
        # load the yaml data
        fp = open('src/richmond/webapp/api/test_data/devquiz.yaml', 'r')
        self.yaml_conversation = ''.join(fp.readlines())
    
    def tearDown(self):
        pass
    
    def test_creation_of_conversation(self):
        """
        Conversations should be able to be created by POSTing to the api
        """
        resp = self.client.post(reverse('api:conversation'), self.yaml_conversation,
                            content_type="application/x-yaml")
        self.assertContains(resp, 'Created', status_code=201)
        
        resp = self.client.get(reverse('api:conversation'))
        self.assertEquals(resp.status_code, 405)
    
    def test_sms_receipts(self):
        """
        Receipts received from clickatell should update the status
        """
        [sms] = mock_sent_messages(self.user, count=1)
        self.assertEquals(sms.delivery_status, 0)
        resp = self.client.post(reverse('api:sms-receipt'), {
            'apiMsgId': 'a' * 32,
            'cliMsgId': sms.pk,
            'status': 8, # OK
            'to': '27123456789',
            'from': '27123456789',
            'timestamp': int(time()),
            'charge': 0.3
        })
        sms = SentSMS.objects.get(pk=sms.pk) # reload
        self.assertEquals(sms.delivery_status, 8)
        self.assertEquals(resp.status_code, 201)
    
    def test_sms_sending(self):
        self.assertEquals(SentSMS.objects.count(), 0)
        resp = self.client.post(reverse('api:sms-send'), {
            'to_msisdn': '27123456789',
            'from_msisdn': '27123456789',
            'message': 'yebo',
        })
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(SentSMS.objects.count(), 1)
    
    def test_batch_sms_sending(self):
        self.assertEquals(SentSMS.objects.count(), 0)
        resp = self.client.post(reverse('api:sms-send'), {
            'to_msisdn': ['27123456780','27123456781','27123456782'],
            'from_msisdn': '27123456789',
            'message': 'yebo'
        })
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(SentSMS.objects.count(), 3)
    
    def test_template_sms_sending(self):
        self.assertEquals(SentSMS.objects.count(), 0)
        resp = self.client.post(reverse('api:sms-template-send'), {
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
        resp = self.client.post(reverse('api:sms-receive'), {
            'to': '27123456789',
            'from': '27123456789',
            'moMsgId': 'a' * 12,
            'api_id': 'b' * 12,
            'text': 'hello world',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S") # MySQL format
        })
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(ReceivedSMS.objects.count(), 1)

class SentSMSStatusTestCase(TestCase):
    
    fixtures = ['user_set', 'sentsms_set']
    
    def setUp(self):
        self.client = APIClient()
        self.client.login('api', 'password')
        self.user = User.objects.get(username='api')
    
    def tearDown(self):
        pass
    
    def test_sms_status_list(self):
        mock_sent_messages(self.user, count=60)
        resp = self.client.get(reverse('api:sms-status-list'), {
            'limit': 40
        })
        from django.utils import simplejson
        data = simplejson.loads(resp.content)
        self.assertEquals(len(data), 40) # respects the limit
        self.assertEquals(resp.status_code, 200)
    
    def test_sms_status_list_since(self):
        """
        Sorry this test needs some explanation. In the SentSMS model I'm using
        Django's `auto_now` and `auto_now_add` options to automatically 
        timestamp the `created_at` and `updated_at` values. Downside of this
        is that you now no longer can set these values from the code. The 
        fixture has a `SentSMS` entry from 2009. I'm using that date to make
        sure the `since` parameter gives us back that entry as well instead
        of only the most recent 50 ones (which I create manually in this test).
        """
        january_2009 = datetime(2009,01,01,0,0,0)
        new_smss = mock_sent_messages(self.user, count=50)
        resp = self.client.get(reverse('api:sms-status-list'), {
            'since': january_2009
        })
        from django.utils import simplejson
        data = simplejson.loads(resp.content)
        self.assertEquals(len(data), 51) # respects the `since` parameter
                                        # overriding the `limit` parameter.
                                        # On top of the 50 newly created
                                        # entries it should also return the 
                                        # 51st entry which is one from 2009
                                        # in the fixtures file.
        self.assertEquals(resp.status_code, 200)
    
    def test_single_status(self):
        sent_sms = SentSMS.objects.latest('created_at')
        resp = self.client.get(reverse('api:sms-status', kwargs={
            "sms_id": sent_sms.pk
        }))
        from django.utils import simplejson
        json_sms = simplejson.loads(resp.content)[0]
        self.assertEquals(json_sms['to_msisdn'], sent_sms.to_msisdn)
        self.assertEquals(json_sms['from_msisdn'], sent_sms.from_msisdn)
        self.assertEquals(json_sms['message'], sent_sms.message)
        self.assertEquals(json_sms['delivery_status'], sent_sms.delivery_status)
        self.assertEquals(resp.status_code, 200)
        
    
class URLCallbackTestCase(TestCase):
    
    fixtures = ['user_set']
    
    def setUp(self):
        self.client = APIClient()
        self.client.login(username='api', password='password')
        # create the user we need to be authorized
        self.user = User.objects.get(username='api')
    
    def tearDown(self):
        pass
    
    def test_setting_callback_url(self):
        self.assertEquals(URLCallback.objects.count(), 0)
        resp = self.client.put(reverse('api:url-callbacks'), {
            'sms_received': 'http://localhost/url/sms/received',
            'sms_receipt': 'http://localhost/url/sms/receipt',
        })
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(URLCallback.objects.count(), 2)