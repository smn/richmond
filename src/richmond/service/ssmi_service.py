from zope.interface import implements

from twisted.python import log
from twisted.python.log import logging
from twisted.application.service import IServiceMaker, Service
from twisted.internet import reactor, protocol, defer
from ssmi.client import SSMIFactory, SSMIClient

class RichmondSSMIProtocol(SSMIClient):
    """
    Subclassing the protocol to avoid me having to
    work with callbacks to do authorization
    """
    def __init__(self, username, password, handler_class):
        self.callback = handler_class()
        self._ussd_callback = self.callback.ussd_callback
        self._sms_callback = self.callback.sms_callback
        self._errback = self.callback.errback
        self._username = username
        self._password = password
        # ugh, can't do normal super() call because twisted's protocol.Factory
        # is an old style class that doesn't subclass object.
        SSMIClient.__init__(self)
    
    def connectionMade(self, *args, **kwargs):
        SSMIClient.connectionMade(self, *args, **kwargs)
        self.factory.onConnectionMade.callback(self)
    
    def connectionLost(self, *args, **kwargs):
        SSMIClient.connectionLost(self, *args, **kwargs)
        self.factory.onConnectionLost.callback(self)
    

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
        
        self.onConnectionMade = defer.Deferred()
        self.onConnectionLost = defer.Deferred()
        
        if not isinstance(self.port, int):
            raise RuntimeError, 'port should be an integer'
    
    def startService(self):
        factory = RichmondSSMIFactory(self.username, self.password, self.callback_class)
        factory.onConnectionMade = self.onConnectionMade
        factory.onConnectionLost = self.onConnectionLost
        self.client_connection = reactor.connectTCP(self.host, self.port, factory)
        log.msg("starting ssmi service")
    
    def stopService(self):
        self.client_connection.disconnect()
        log.msg("stopping ssmi service")
    
