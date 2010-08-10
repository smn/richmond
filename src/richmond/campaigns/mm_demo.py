from richmond.services.truteq.base import Publisher, Consumer, SessionType
from richmond.services.worker import PubSubWorker
from twisted.python import log

from alexandria.client import Client
from alexandria.sessions.backend import DBBackend
from alexandria.sessions.manager import SessionManager
from alexandria.dsl.core import MenuSystem, prompt, end
from alexandria.dsl.validators import pick_one

class VumiDBClient(Client):
    
    def __init__(self, msisdn, send_callback):
        self.id = msisdn
        self.session_manager = SessionManager(client=self, backend=DBBackend())
        self.session_manager.restore()
        self.send_callback = send_callback
    
    def send(self, text, end_session=False):
        if end_session:
            reply_type = SessionType.end
            self.deactivate()
        else:
            reply_type = SessionType.existing
        return self.send_callback(self.id, text, reply_type)


class VumiConsumer(Consumer):
    
    """
    Describe the menu system we're running
    """
    menu = MenuSystem(
        prompt('Hello! What is your name?'),
        prompt('In what industry are you involved?', options=(
            'Retail',
            'Marketing',
            'Financial/Banking',
            'IT/Technology',
            'FMCG',
            'Travel',
            'Media',
            'Other',
        ), validator=pick_one),
        prompt('How are you finding the conference?', options=(
            'Meeting my expectations',
            'Exceeding my expectations',
            'Not meeting my expectations',
        ), validator=pick_one),
        end('Thanks!')
    )
    
    def new_ussd_session(self, msisdn, message):
        client = VumiDBClient(msisdn, self.reply)
        client.answer(str(message), self.menu)
    
    def existing_ussd_session(self, msisdn, message):
        client = VumiDBClient(msisdn, self.reply)
        client.answer(str(message), self.menu)
    
    def timed_out_ussd_session(self, msisdn, message):
        log.msg('%s timed out, removing client' % msisdn)
        client = VumiDBClient(msisdn, self.reply)
        client.deactivate()
    
    def end_ussd_session(self, msisdn, message):
        log.msg('%s ended the session, removing client' % msisdn)
        client = VumiDBClient(msisdn, self.reply)
        client.deactivate()
    

class VumiUSSDWorker(PubSubWorker):
    consumer_class = VumiConsumer
    publisher_class = Publisher
