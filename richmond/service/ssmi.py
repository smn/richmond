from zope.interface import implements

from twisted.python import log
from twisted.application.service import IServiceMaker, Service

class SSMIService(Service):
    implements(IServiceMaker)
    
    def startService(self):
        log.msg("starting ssmi service")

    def stopService(self):
        log.msg("stopping ssmi service")
