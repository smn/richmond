from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

class ApiViewTestCase(TestCase):
    
    def setUp(self):
        fp = open('src/richmond/webapp/api/test_data/devquiz.yaml', 'r')
        self.yaml_conversation = ''.join(fp.readlines())
    
    def tearDown(self):
        pass
    
    def test_creation_of_conversation(self):
        """
        Conversations should be able to be created by POSTing to the api
        """
        client = Client()
        resp = client.post(reverse('api:conversation'), self.yaml_conversation,
                            content_type="text/yaml")
        self.assertContains(resp, 'OK')
        
        resp = client.get(reverse('api:conversation'))
        self.assertContains(resp, 'Method not allowed', status_code=405)