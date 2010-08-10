from richmond.services.truteq.base import Publisher, Consumer, SessionType
from richmond.services.worker import PubSubWorker
from twisted.python import log

from alexandria.client import Client
from alexandria.sessions.backend import DBBackend
from alexandria.sessions.manager import SessionManager
from alexandria.sessions.db import models
from alexandria.dsl.core import MenuSystem, prompt, end, case
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

def save_to_session(key, value):
    while True:
        ms, session = yield
        session[key] = value
        yield False, False

def industry_stats():
    return "These are the industry stats!"

def expectations_stats():
    return "These are the expectations!"

def returning_user(menu, session):
    return session.get('completed', False)

def new_user(*args, **kwargs):
    return not returning_user(*args, **kwargs)

class VumiConsumer(Consumer):
    
    """
    Describe the menu system we're running
    """
    menu = MenuSystem(
        case(
            (new_user, prompt('Welcome to the Praekelt Star menu system. ' +\
                                    'What is your first name?', save_as='name')),
            (returning_user, prompt('Welcome back %(name)s'))
        ),
        case(
            (new_user, prompt('What industry are you from?', options=(
                'Marketing',
                'Industry',
                'Retail',
                'Financial/Banking',
                'IT/Technology',
                'Media',
                'Other'
            ), save_as='industry', validator=pick_one)),
            (returning_user, prompt(industry_stats(), options=('Continue',)))
        ),
        case(
            (new_user, prompt('How are you finding the conference?', options=(
                'Meeting my expectations',
                'Exceeding my expectations',
                'Not meeting my expectations',
            ), save_as='expectations', validator=pick_one)),
            (returning_user, prompt(expectations_stats(), options=('Continue',)))
        ),
        save_to_session('completed', True),
        # sms(
        #     'Hi %(name)s want to know more about Vumi and Star menus? ' + \
        #     'Visit http://www.praekelt.com'
        # ),
        end('Thanks for taking part. You can view real-time statistics on ' + \
            'the Praekelt screens, or by dialing back into the Star menu ' + \
            ' system!')
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
