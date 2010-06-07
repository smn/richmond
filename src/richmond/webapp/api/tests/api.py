from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from time import time
from datetime import datetime, timedelta

from richmond.webapp.api.models import *
from richmond.webapp.api.tests.utils import APIClient

import logging
LOG_FILENAME = 'logs/richmond.testing.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

class PyCurlBugTestCase(TestCase):
    
    def test_callback_unicode_warning(self):
        from richmond.webapp.api.utils import callback
        self.assertRaises(RuntimeError, callback, 'http://localhost/', (
            (u'key', 'value'), # unicode keys or values aren't allowed
        ))
        self.assertRaises(RuntimeError, callback, 'http://localhost/', (
            ('key', u'value'), # unicode keys or values aren't allowed
        ))

class ConversationHandlerTestCase(TestCase):
    
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
    

class URLCallbackHandlerTestCase(TestCase):
    
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
        resp = self.client.post(reverse('api:clickatell:sms-receive'), {
            'to': '27123456789',
            'from': '27123456789',
            'moMsgId': 'a' * 12,
            'api_id': 'b' * 12,
            'text': 'hello world',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S") # MySQL format
        })
        # this should show up in the testing log because pycurl can't
        # connect to the given host for the callback


