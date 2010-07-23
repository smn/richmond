from urllib import urlopen, urlencode, quote
import logging

class TechsysException(Exception): pass

class Techsys(object):
    
    def __init__(self, url, bind):
        self.url = url
        self.bind = bind
    
    def send_sms(self, recipient, text):
        post = {
            'bind': self.bind, 
            'msisdn': recipient, 
            'text': text,
        }
        
        response = urlopen(self.url, urlencode(post)).read()
        logging.debug('Received Techsys response: %s' % response)
        if 'Message queued successfully' not in response:
            raise TechsysException('SMS sending failed: %s' % response)
        return response