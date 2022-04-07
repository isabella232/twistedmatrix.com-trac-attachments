import os.path
from StringIO import StringIO
import shutil,sys,os,re
import errno

from zope.interface import implements

from twisted.trial import unittest
from twisted.protocols import basic, policies
from twisted.internet import reactor, protocol, defer, error
from twisted.internet.interfaces import IConsumer
from twisted.cred import portal, checkers, credentials
from twisted.python import failure, filepath
from twisted.test import proto_helpers

from twisted.protocols import ftp, loopback


class FTPServerTestCase(unittest.TestCase):
    """
    Simple tests for an FTP server with the default settings.

    @ivar clientFactory: class used as ftp client.
    """
    clientFactory = ftp.FTPClientBasic


    def tearDown(self):
        # Clean up sockets
        self.client.transport.loseConnection()
        d = defer.maybeDeferred(self.port.stopListening)
        d.addCallback(self.ebTearDown)
        return d

    def ebTearDown(self, ignore):
        del self.serverProtocol
        # Clean up temporary directory
        shutil.rmtree(self.directory)


    def assertCommandResponse(self, command, expectedResponseLines,
                              chainDeferred=None):
        """Asserts that a sending an FTP command receives the expected
        response.

        Returns a Deferred.  Optionally accepts a deferred to chain its actions
        to.
        """
        if chainDeferred is None:
            chainDeferred = defer.succeed(None)

        print "> %s" % command
        def queueCommand(ignored):
            d = self.client.queueStringCommand(command)
            def gotResponse(responseLines):
                print "< %s" % responseLines
                self.assertEquals(expectedResponseLines, responseLines)
            return d.addCallback(gotResponse)
        return chainDeferred.addCallback(queueCommand)


    def _anonymousLogin(self):
        d = self.assertCommandResponse(
            'USER anonymous',
            ['331 Guest login ok, type your email address as password.'])
        return self.assertCommandResponse(
            'PASS test@twistedmatrix.com',
            ['230 Anonymous login ok, access restrictions apply.'],
            chainDeferred=d)

    
    def test_portRangeDoesntWork(self):
        """
        L{FTP.passivePortRange} should determine the ports which
        L{FTP.getDTPPort} attempts to bind. If no port from that iterator can
        be bound, L{error.CannotListenError} should be raised, otherwise the
        first successful result from L{FTP.listenFactory} should be returned.
        """
        
        
        # Create a directory
        self.directory = self.mktemp()
        os.mkdir(self.directory)

        # Start the server
        p = portal.Portal(ftp.FTPRealm(self.directory))
        p.registerChecker(checkers.AllowAnonymousAccess(),
                          credentials.IAnonymous)
        
        
        self.factory = ftp.FTPFactory(portal=p)
        
        self.factory.passivePortRange = xrange(8022,8042)
        
        self.port = reactor.listenTCP(0, self.factory, interface="127.0.0.1")

        # Hook the server's buildProtocol to make the protocol instance
        # accessible to tests.
        buildProtocol = self.factory.buildProtocol
        d1 = defer.Deferred()
        def _rememberProtocolInstance(addr):
            protocol = buildProtocol(addr)
            self.serverProtocol = protocol.wrappedProtocol
            d1.callback(None)
            return protocol
        self.factory.buildProtocol = _rememberProtocolInstance

        # Connect a client to it
        portNum = self.port.getHost().port
        clientCreator = protocol.ClientCreator(reactor, self.clientFactory)
        d2 = clientCreator.connectTCP("127.0.0.1", portNum)
        def gotClient(client):
            self.client = client
        d2.addCallback(gotClient)
        return defer.gatherResults([d1, d2])
        
        
        
        def listenFactory(portNumber, factory):
            if portNumber in (22032, 22033, 22034):
                raise error.CannotListenError('localhost', portNumber, 'error')
            return portNumber
        self.serverProtocol.listenFactory = listenFactory

        port = self.serverProtocol.getDTPPort(protocol.Factory())
        self.assertEquals(port, 0)

        

    def test_portRangeWorks(self):
        """
        L{FTP.passivePortRange} should determine the ports which
        L{FTP.getDTPPort} attempts to bind. If no port from that iterator can
        be bound, L{error.CannotListenError} should be raised, otherwise the
        first successful result from L{FTP.listenFactory} should be returned.
        """
        
        
        # Create a directory
        self.directory = self.mktemp()
        os.mkdir(self.directory)

        # Start the server
        p = portal.Portal(ftp.FTPRealm(self.directory))
        p.registerChecker(checkers.AllowAnonymousAccess(),
                          credentials.IAnonymous)
        
        
        class goodFTPFactory(ftp.FTPFactory):
                
            def buildProtocol(self, addr):
        
                p = policies.LimitTotalConnectionsFactory.buildProtocol(self, addr)
                if p is not None:
                    p.wrappedProtocol.portal = self.portal
                    p.wrappedProtocol.timeOut = self.timeOut
                    p.wrappedProtocol.passivePortRange = self.passivePortRange
                   
                return p
        
        
        self.factory = goodFTPFactory(portal=p)
        
        self.factory.passivePortRange = xrange(8022,8042)
        
        self.port = reactor.listenTCP(0, self.factory, interface="127.0.0.1")

        # Hook the server's buildProtocol to make the protocol instance
        # accessible to tests.
        buildProtocol = self.factory.buildProtocol
        d1 = defer.Deferred()
        def _rememberProtocolInstance(addr):
            protocol = buildProtocol(addr)
            self.serverProtocol = protocol.wrappedProtocol
            d1.callback(None)
            return protocol
        self.factory.buildProtocol = _rememberProtocolInstance

        # Connect a client to it
        portNum = self.port.getHost().port
        clientCreator = protocol.ClientCreator(reactor, self.clientFactory)
        d2 = clientCreator.connectTCP("127.0.0.1", portNum)
        def gotClient(client):
            self.client = client
        d2.addCallback(gotClient)
        return defer.gatherResults([d1, d2])
        
        
        
        def listenFactory(portNumber, factory):
            if portNumber in (22032, 22033, 22034):
                raise error.CannotListenError('localhost', portNumber, 'error')
            return portNumber
        self.serverProtocol.listenFactory = listenFactory

        port = self.serverProtocol.getDTPPort(protocol.Factory())
        self.assertEquals(port, 8022)

        
        
        
        
        
        
        



if __name__ == "__main__":

    from twisted.trial import runner,reporter
    suite = runner.TestLoader().loadClass(FTPServerTestCase)
    
    result = reporter.Reporter(stream=sys.stdout)
    
    suite.run(result)
    
    result.done()