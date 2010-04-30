from zope.interface import implements

from twisted.python import log
from twisted.application.service import IServiceMaker, Service

class AMQPService(Service):
    implements(IServiceMaker)
    
    def startService(self):
        log.msg("starting amqp service")

    def stopService(self):
        log.msg("stopping amqp service")
