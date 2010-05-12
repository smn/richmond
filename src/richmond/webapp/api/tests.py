from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
import base64

from richmond.webapp.api.models import SMS

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
        resp = self.client.post(reverse('api:sms-receipt'))
        print resp.content
        self.assertEquals(resp.status_code, 201)
    
    def test_sms_sending(self):
        resp = self.client.post(reverse('api:sms-send'), {
            'to_msisdn': '27123456789',
            'from_msisdn': '27123456789',
            'message': 'yebo',
        })
        self.assertEquals(resp.status_code, 200)
        self.assertTrue(SMS.objects.count())
    
    def test_sms_receiving(self):
        resp = self.client.post(reverse('api:sms-receive'))
        self.assertEquals(resp.status_code, 201)