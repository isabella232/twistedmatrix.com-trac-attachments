from twisted.internet import iocpreactor
iocpreactor.install()
from twisted.internet import protocol,defer,reactor
from twisted.protocols import policies
from twisted.trial import unittest

smallChunk = b'X'
smallLen = len(smallChunk)
ops = 2*1024*1024
totalLen = smallLen*ops

class FireOnClose(policies.ProtocolWrapper):
    """A wrapper around a protocol that makes it fire a deferred when
    connectionLost is called.
    """
    def connectionLost(self, reason):
        policies.ProtocolWrapper.connectionLost(self, reason)
        self.factory.deferred.callback(None)


class FireOnCloseFactory(policies.WrappingFactory):
    protocol = FireOnClose

    def __init__(self, wrappedFactory):
        policies.WrappingFactory.__init__(self, wrappedFactory)
        self.deferred = defer.Deferred()



class LargeProtocol(protocol.Protocol):
    def dataReceived(self,data):
        self.transport.write(data)
        self.factory.dataLen += len(data)

    def connectionLost(self,reason):
        self.factory.done = 1

class LargeServerFactory(protocol.Factory):
    dataLen = 0
    maxLen = 0
    def buildProtocol(self,addr):
        p = LargeProtocol()
        p.factory = self
        return p

class LargeClientProtocol(protocol.Protocol):
    def connectionMade(self):
        reactor.callLater(1,self.transport.write,smallChunk*ops)
        self.checkd = None
        
    def dataReceived(self,data):
        self.factory.dataBuffer += data
        if not self.checkd:
            self.checkd = reactor.callLater(1, self.extraCheck)
            
            

    def connectionLost(self,reason):
        self.factory.done = 1
        if self.checkd:
            self.checkd.cancel()
            self.checkd = None

    def extraCheck(self):
        if len(self.factory.dataBuffer) == totalLen:
            self.factory.normal = True
            self.transport.loseConnection()
        elif len(self.factory.dataBuffer) > totalLen:
            self.factory.normal = False
            self.transport.loseConnection()
        else:
            pass
        self.checkd = None


class LargeClientFactory(protocol.ClientFactory):
    def __init__(self):
        self.done = 0
        self.dataBuffer = ''
        self.normal = False
        
    def buildProtocol(self,addr):
        p = LargeClientProtocol()
        p.factory = self
        return p


class LargeTestCase(unittest.TestCase):
    """Test that buffering large amounts of data works.
    """

    def testWriter(self):
        f = LargeServerFactory()
        f.done = 0
        f.problem = 0
        f.maxLen = totalLen
        wrappedF = FireOnCloseFactory(f)
        p = reactor.listenTCP(12345, wrappedF, interface="127.0.0.1")
        self.addCleanup(p.stopListening)
        n = p.getHost().port
        #n = 12345
        clientF = LargeClientFactory()
        wrappedClientF = FireOnCloseFactory(clientF)
        reactor.connectTCP("127.0.0.1", n, wrappedClientF)

        d = defer.gatherResults([wrappedClientF.deferred])
        def check(ignored):
            self.failUnless(clientF.normal,
                            "client received data is abnormal "
                            "(%d != %d)" % (len(clientF.dataBuffer), totalLen))
            self.failUnless(clientF.done,
                            "client didn't see connection dropped")
        return d.addCallback(check)

