from zope.interface import implements

from twisted.python import log
from twisted.application.service import IServiceMaker, Service
from twisted.internet import reactor, protocol
from ssmi.client import SSMIFactory, SSMIClient

class SSMIService(Service):
    implements(IServiceMaker)
    
    def __init__(self, username, password, host, port):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        if not isinstance(self.port, int):
            raise RuntimeError, 'port should be an integer'
    
    def got_protocol(self, prot):
        log.msg("GOT PROTOCOL!")
        prot.app_setup(self.username, self.password, self.ussd_callback,
                                            self.sms_callback, self.errback)    
    
    def ussd_callback(self, *args, **kwargs):
        log.msg("ussd_callback: %s, %s" % (args, kwargs))
    
    def sms_callback(self, *args, **kwargs):
        log.msg("sms_callback: %s, %s" % (args, kwargs))
    
    def errback(self, *args, **kwargs):
        log.msg("errback: %s, %s" % (args, kwargs))

    def startService(self):
        client_creator = protocol.ClientCreator(reactor, SSMIClient)
        deferred = client_creator.connectTCP(self.host, self.port)
        deferred.addCallback(self.got_protocol)
        log.msg("starting ssmi service")

    def stopService(self):
        log.msg("stopping ssmi service")
