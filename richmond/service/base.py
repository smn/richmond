from zope.interface import implements

from twisted.python import log
from twisted.application.service import IServiceMaker, Service
from richmond.service.amqp import AMQPService
from richmond.service.ssmi import SSMIService

class RichmondService(Service):
    implements(IServiceMaker)
    
    def startService(self):
        log.msg("starting richmond service")
        
        self.ssmi = SSMIService()
        self.ssmi.setName("ssmi")
        self.ssmi.startService()
        
        self.amqp = AMQPService()
        self.amqp.setName("amqp")
        self.amqp.startService()

    def stopService(self):
        log.msg("stopping richmond service")
        self.ssmi.stopService()
        self.amqp.stopService()
