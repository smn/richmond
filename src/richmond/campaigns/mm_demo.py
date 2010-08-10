from richmond.services.truteq.base import Publisher, Consumer, SessionType
from richmond.services.worker import PubSubWorker
from twisted.python import log

from alexandria.client import Client
from alexandria.sessions.backend import DBBackend
from alexandria.sessions.manager import SessionManager
from alexandria.sessions.db import models
from alexandria.sessions.db.views import _get_data
from alexandria.dsl.core import MenuSystem, prompt, end, case
from alexandria.dsl.validators import pick_one

INDUSTRY_OPTIONS = (
    'Marketing',
    'Industry',
    'Retail',
    'Financial/Banking',
    'IT/Technology',
    'Media',
    'Other'
)

EXPECTATIONS_OPTIONS = (
    'Meeting my expectations',
    'Exceeding my expectations',
    'Not meeting my expectations',
)

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
        if callable(value):
            session[key] = value()
        else:
            session[key] = value
        yield False, False

def industry_stats():
    data = _get_data().get('industry', {})
    total = float(sum(data.values()))
    if total:
        return "\n".join(["%s: %.0f%%" % (option, (data.get(option, 0) / total) * 100) 
                        for option in INDUSTRY_OPTIONS])
    else:
        return "Not enough data yet"

def expectations_stats():
    data = _get_data().get('expectations', {})
    total = float(sum(data.values()))
    if total:
        return "\n".join(["%s: %.0f%%" % (option, (data.get(option, 0) / total) * 100) 
                        for option in EXPECTATIONS_OPTIONS])
    else:
        return "Not enough data yet"
    

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
            (returning_user, prompt('Welcome back %(name)s', parse=True))
        ),
        save_to_session('industry_stats', industry_stats),
        case(
            (new_user, prompt('What industry are you from?', 
                                options=INDUSTRY_OPTIONS, 
                                save_as='industry', 
                                validator=pick_one)),
            (returning_user, prompt("%(industry_stats)s", 
                                        parse=True,
                                        options=('Continue',)))
        ),
        save_to_session('expectations_stats', expectations_stats),
        case(
            (new_user, prompt('How are you finding the conference?', 
                                options=EXPECTATIONS_OPTIONS, 
                                save_as='expectations', 
                                validator=pick_one)),
            (returning_user, prompt("%(expectations_stats)s", 
                                        parse=True, 
                                        options=('Continue',)))
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
