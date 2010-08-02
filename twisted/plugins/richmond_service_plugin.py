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
        reactor.callLater(1, self.publisher.publish, dictionary)

class ExamplePublisher(Publisher):
    
    def publish(self, dictionary):
        log.msg("Publishing JSON %s" % dictionary)
        super(ExamplePublisher, self).publish(dictionary)

class ExampleWorker(Worker):
    
    @inlineCallbacks
    def startWorker(self):
        log.msg("Starting the ExampleService")
        self.publisher = yield self.start_publisher(ExamplePublisher)
        self.consumer = yield self.start_consumer(ExampleConsumer, self.publisher)
        reactor.callLater(0, self.publisher.publish, {'hello': 'world'})
    
    def stopWorker(self):
        log.msg("Stopping the ExampleService")
    


class RichmondService(Service):
    
    def __init__(self, options):
        self.options = options
    
    def startService(self):
        log.msg("Starting RichmondService")
        host = self.options.pop('hostname')
        port = self.options.pop('port')
        creator = WorkerCreator(reactor, ExampleWorker, **self.options)
        creator.connectTCP(host, port)
    
    def stopService(self):
        log.msg("Stopping RichmondService")
    


class BasicSet(Options):
    optParameters = Options.optParameters + [
        ["extra_parameters", "ap", "default", "An example extra parameter"],
    ]

class RichmondServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "richmond_default_plugin"
    description = "Start a Richmond service"
    options = BasicSet
    
    def makeService(self, options):
        return RichmondService(options)

serviceMaker = RichmondServiceMaker()
