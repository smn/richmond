from zope.interface import implements
from twisted.python import log
from twisted.application.service import IServiceMaker, Service
from twisted.plugin import IPlugin
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import reactor

from richmond.service import Options, WorkerCreator, Worker, Consumer, Publisher

class ExampleConsumer(Consumer):
    
    def __init__(self, publisher):
        self.publisher = publisher
    
    def consume_json(self, dictionary):
        log.msg("Consumed JSON %s" % dictionary)
        reactor.callLater(1, self.publisher.publish_json, dictionary)
    

class ExamplePublisher(Publisher):
    
    def publish_json(self, dictionary):
        log.msg("Publishing JSON %s" % dictionary)
        super(ExamplePublisher, self).publish_json(dictionary)
    

class ExampleWorker(Worker):
    
    # inlineCallbacks, TwistedMatrix's fancy way of allowing you to write
    # asynchronous code as if it was synchronous by the nifty use of
    # coroutines.
    # See: http://twistedmatrix.com/documents/10.0.0/api/twisted.internet.defer.html#inlineCallbacks
    @inlineCallbacks
    def startWorker(self):
        log.msg("Starting the ExampleWorker")
        # create the publisher
        self.publisher = yield self.start_publisher(ExamplePublisher)
        # when it's done, create the consumer and pass it the publisher
        self.consumer = yield self.start_consumer(ExampleConsumer, self.publisher)
        # publish something into the queue for the consumer to pick up.
        reactor.callLater(0, self.publisher.publish_json, {'hello': 'world'})
    
    def stopWorker(self):
        log.msg("Stopping the ExampleWorker")
    


# This is the actual service that is started, this the thing that runs
# in the background and starts a worker.
class RichmondService(Service):
    
    # it receives the dictionary of options from the command line
    def __init__(self, options):
        self.options = options
    
    # Twistd calls this methods at boot
    def startService(self):
        log.msg("Starting RichmondService")
        host = self.options.pop('hostname')
        port = self.options.pop('port')
        # the worker creator starts workers, you give it the reactor
        # which controls the eventloop, what class you want to start
        # and what options you want to pass along
        creator = WorkerCreator(ExampleWorker, **self.options)
        # after that you connect it to the AMQP server
        creator.connectTCP(host, port)
    
    # Twistd calls this method at shutdown
    def stopService(self):
        log.msg("Stopping RichmondService")
    


# Extend the default Richmond options with whatever options your service needs
class BasicSet(Options):
    optParameters = Options.optParameters + [
        ["extra_parameters", "ap", "default", "An example extra parameter"],
    ]

# This create the service, runnable on command line with twistd
class RichmondServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    # the name of our plugin, this will be the subcommand for twistd
    # e.g. $ twistd -n richmond_default_plugin --option1= ...
    tapname = "richmond_default_plugin"
    # description, also for twistd
    description = "Start a Richmond service"
    # what command line options does this service expose
    options = BasicSet
    
    def makeService(self, options):
        return RichmondService(options)

# Announce the plugin as a service maker for twistd 
# See: http://twistedmatrix.com/documents/current/core/howto/tap.html
serviceMaker = RichmondServiceMaker()
