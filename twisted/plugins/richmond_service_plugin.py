from zope.interface import implements
from twisted.python import usage, log
from twisted.application.service import IServiceMaker, MultiService
from twisted.plugin import IPlugin
from richmond.utils import load_class_by_string, filter_options_on_prefix

class Options(usage.Options):
    optParameters = [
        ["service", "s", None, "Connect a service to Richmond"],
        ["config", "c", None, "Configuration file for the service to start"]
    ]

class RichmondServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "richmond_service"
    description = "Start a Richmond service"
    options = Options
    
    def makeService(self, options):
        required_arguments = ['service', 'config']
        for argument in required_arguments:
            if argument not in options:
                raise RuntimeError, 'Please specify what %s to start' % argument
        service_class = load_class_by_string(options.pop('service'))
        return service_class(options.pop('config'))

serviceMaker = RichmondServiceMaker()
