from zope.interface import implements
from twisted.python import usage, log
from twisted.application.service import IServiceMaker, MultiService
from twisted.plugin import IPlugin
from richmond.utils import load_class_by_string, filter_options_on_prefix

class Options(usage.Options):
    optParameters = [
        ["service", "s", None, "Connect a service to Richmond"],
        ["worker", "w", None, "Connect a worker to Richmond"]
    ]
    
    def parseArgs(self, *args):
        """Parses service & worker specific arguments"""
        options=dict(arg.split("=") for arg in args)
        self.service_options = filter_options_on_prefix(options, "service-")
        self.worker_options = filter_options_on_prefix(options, "worker-")
    

class RichmondServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "richmond_service"
    description = "Start a Richmond service and/or worker pair"
    options = Options
    
    def makeService(self, options):
        multi_service = MultiService()
        
        service_class_name = options.get('service')
        if service_class_name:
            service_class = load_class_by_string(options.get('service'))
            service = service_class(**options.service_options)
            multi_service.addService(service)
        
        worker_class_name = options.get('worker')
        if worker_class_name:
            worker_class = load_class_by_string(options.get('worker'))
            worker = worker_class(**options.worker_options)
            multi_service.addService(service)
        
        return multi_service

serviceMaker = RichmondServiceMaker()
