from zope.interface import implements

from twisted.python import log
import logging
from twisted.application.service import IServiceMaker, Service
from twisted.internet import reactor, protocol
from ssmi.client import SSMIFactory, SSMIClient

class RichmondSSMIProtocol(SSMIClient):
    """
    Subclassing the protocol to avoid me having to
    work with callbacks to do authorization
    """
    def __init__(self, username, password, handler_class):
        callback = handler_class()
        self._ussd_callback = callback.ussd_callback
        self._sms_callback = callback.sms_callback
        self._errback = callback.errback
        self._username = username
        self._password = password
        # ugh, can't do normal super() call because twisted's protocol.Factory
        # is an old style class that doesn't subclass object.
        SSMIClient.__init__(self)
    

class RichmondSSMIFactory(SSMIFactory):
    """
    Subclassed the factory to allow me to work with my custom subclassed
    protocol
    """
    protocol = RichmondSSMIProtocol
    
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
    
    def buildProtocol(self, addr):
        prot = self.protocol(*self.args, **self.kwargs)
        prot.factory = self
        log.msg('SSMIFactory Connected.', logLevel=logging.DEBUG)
        log.msg('SSMIFactory Resetting reconnection delay', logLevel=logging.DEBUG)
        self.resetDelay()
        return prot
        

class SSMICallback(object):
    
    def ussd_callback(self, *args, **kwargs):
        log.msg("Unhandled ussd_callback: %s, %s" % (args, kwargs), logLevel=logging.DEBUG)
    
    def sms_callback(self, *args, **kwargs):
        log.msg("Unhandled sms_callback: %s, %s" % (args, kwargs), logLevel=logging.DEBUG)
    
    def errback(self, *args, **kwargs):
        log.msg("Unhandled errback: %s, %s" % (args, kwargs), logLevel=logging.DEBUG)
    

class SSMIService(Service):
    implements(IServiceMaker)
    
    def __init__(self, username, password, host, port, callback_class=SSMICallback):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.callback_class = callback_class
        if not isinstance(self.port, int):
            raise RuntimeError, 'port should be an integer'
    
    def startService(self):
        factory = RichmondSSMIFactory(self.username, self.password, self.callback_class)
        self.client_connection = reactor.connectTCP(self.host, self.port, factory)
        log.msg("starting ssmi service")
    
    def stopService(self):
        self.client_connection.disconnect()
        log.msg("stopping ssmi service")
    
