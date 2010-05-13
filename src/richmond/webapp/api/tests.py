from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
import base64
from time import time
from datetime import datetime

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


class ApiViewTestCase(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        self.client.login(username='api', password='password')
        # create the user we need to be authorized
        self.user = User.objects.create_user('api', 'api@domain.com', 'password')
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
        sms = SentSMS.objects.create(to_msisdn='27123456789',
                                    from_msisdn='27123456789',
                                    message='testing api')
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