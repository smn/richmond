import yaml
from zope.interface import implements
from twisted.python import log
from twisted.application.service import IServiceMaker, Service
from twisted.plugin import IPlugin
from twisted.internet import reactor

from richmond.service import Options, WorkerCreator
from richmond.utils import load_class_by_string
from richmond.errors import RichmondError

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
        # the worker creator starts workers, give it what class you 
        # want to start and what options you want to pass along
        worker_class_name = self.options.pop("worker_class")
        if not worker_class_name:
            raise RichmondError, "please specify --worker_class"
        
        # load the config file if specified
        config_file = self.options.pop('config')
        if config_file:
            with file(config_file, 'r') as stream:
                self.options.update({
                    'config': yaml.load(stream)
                })
        
        worker_class = load_class_by_string(worker_class_name)
        creator = WorkerCreator(worker_class, **self.options)
        # after that you connect it to the AMQP server
        creator.connectTCP(host, port)
    
    # Twistd calls this method at shutdown
    def stopService(self):
        log.msg("Stopping RichmondService")
    


# Extend the default Richmond options with whatever options your service needs
class BasicSet(Options):
    optParameters = Options.optParameters + [
        ["worker_class", None, None, "class of a worker to start"],
        ["config", None, None, "YAML config file to load"],
    ]

# This create the service, runnable on command line with twistd
class RichmondServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    # the name of our plugin, this will be the subcommand for twistd
    # e.g. $ twistd -n richmond_worker_example_2 --option1= ...
    tapname = "start_worker"
    # description, also for twistd
    description = "Start a Richmond worker"
    # what command line options does this service expose
    options = BasicSet
    
    def makeService(self, options):
        return RichmondService(options)

# Announce the plugin as a service maker for twistd 
# See: http://twistedmatrix.com/documents/current/core/howto/tap.html
serviceMaker = RichmondServiceMaker()
