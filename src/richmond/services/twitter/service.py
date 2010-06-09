from richmond.services import base, worker
from twisted.internet.defer import inlineCallbacks
from twisted.python import log
from twittytwister import twitter

class Publisher(worker.Publisher):
    exchange_name = 'richmond'
    routing_key = 'twitter.receive'

class Consumer(worker.Consumer):
    exchange_name = 'richmond'
    exchange_type = 'direct'
    queue_name = 'richmond.twitter.send'
    routing_key = 'twitter.send'
    
class TwitterService(base.RichmondService):
    
    @inlineCallbacks
    def start(self, **options):
        self.options = options
        username = self.options['username']
        password = self.options['password']
        terms = set(self.options['terms'].split())
        
        self.publisher = yield self.create_publisher(Publisher).addErrback(log.err)
        self.consumer = yield self.create_consumer(Consumer).addErrback(log.err)
        self.stream = yield twitter.TwitterFeed(username, password). \
                                track(self.handle_status, terms). \
                                addErrback(log.err)
    
    def status_part_to_dict(self, part, keys=[]):
        return dict([(key, getattr(part,key)) for key in keys])
    
    def handle_status(self, status):
        data = self.status_part_to_dict(status, ['geo','text', 'created_at'])
        data['user'] = self.status_part_to_dict(status.user, 
        [
            'id',  
            'followers_count', 
            'statuses_count',
            'friends_count',
            'location',
            'name',
            'screen_name',
            'url',
            'time_zone',
        ])
        self.publisher.send(data)
    
    def stop(self):
        pass
    