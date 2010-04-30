from zope.interface import implements

from twisted.python import log
from twisted.application.service import IServiceMaker, Service
from richmond.service.amqp import AMQPService
from richmond.service.ssmi import SSMIService

class RichmondService(Service):
    implements(IServiceMaker)
    
    def startService(self):
        log.msg("starting service")
        self.ssmi = SSMIService()
        self.ssmi.setServicParent(self)
        self.ssmi.startService()

    def stopService(self):
        log.msg("stopping service")
        self.ssmi.stopService()
