from richmond.services import base, worker
from richmond.webapp.api.utils import callback
from twisted.internet.defer import inlineCallbacks
from twisted.python import log
from twittytwister import twitter
import pycurl
from cStringIO import StringIO

COUCH_DB_URL = 'http://localhost:5984/twitter'

def post_to_couchdb(json):
    """
    HTTP POST a list of key value tuples to the given URL and 
    return the response
    """
    url = COUCH_DB_URL
    
    data = StringIO()
    ch = pycurl.Curl()
    ch.setopt(pycurl.POST, 1)
    ch.setopt(pycurl.POSTFIELDS, json)
    ch.setopt(pycurl.URL, url)
    ch.setopt(pycurl.VERBOSE, 0)
    ch.setopt(pycurl.HTTPHEADER, [
            "User-Agent: Richmond Twitter Worker Client",
            "Content-Type: application/json"
        ])
    ch.setopt(pycurl.WRITEFUNCTION, data.write)
    ch.setopt(pycurl.FOLLOWLOCATION, 1)
    
    try:
        result = ch.perform()
        resp = data.getvalue()
        log.msg("Posting to %s which returned %s" % (url, resp))
        return (True, resp)
    except pycurl.error, e:
        log.err("Posting to %s resulted in error: %s" % (url, e))
        return (False, e)


class Consumer(worker.Consumer):
    exchange_name = 'richmond'
    exchange_type = 'direct'
    queue_name = 'richmond.twitter.receive'
    routing_key = 'twitter.receive'
    
    def stringify(self, list_of_key_values):
        return [(str(key), str(value)) for key,value in list_of_key_values]
    
    def consume_data(self, message):
        success, response = post_to_couchdb(message.content.body)
        if success:
            self.ack(message)
    
    
class TwitterWorker(base.RichmondService):
    
    @inlineCallbacks
    def start(self, **options):
        self.options = options
        self.consumer = yield self.create_consumer(Consumer).addErrback(log.err)
    
    def stop(self):
        pass
