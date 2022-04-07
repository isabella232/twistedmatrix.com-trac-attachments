from twisted.internet import iocpreactor
iocpreactor.install()

from twisted.internet import protocol,defer,reactor
from twisted.protocols import policies
from twisted.trial import unittest
import time


smallChunk = b'X'
smallLen = len(smallChunk)
packet_size = 130000
totalLen = smallLen*packet_size
maxWrites = 10

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



class SequenceServerProtocol(protocol.Protocol):
    def dataReceived(self,data):
        self.factory.dataLen += len(data)
        # each packet is totalLen in size. Return a single byte to indicate packet received
        while self.factory.dataLen >= totalLen:
            print 'SequenceServerProtocol::dataReceived Echoing back'
            self.transport.write(smallChunk)
            self.factory.dataLen = self.factory.dataLen - totalLen
            
            
    def connectionLost(self,reason):
        print 'Connection lost'
        self.factory.done = 1

class SequenceServerFactory(protocol.Factory):
    dataLen = 0
    def buildProtocol(self,addr):
        p = SequenceServerProtocol()
        p.factory = self
        return p

class SequenceClientProtocol(protocol.Protocol):
    def connectionMade(self):
        print 'SequenceClientProtocol::connectionMade Writing'
        self.writeData()
        
    def dataReceived(self,data):
        print 'SequenceClientProtocol::dataReceived Reading %s echo_count %s len %s' % (len(data), self.factory.echo_count, len(data))
        if len(data) > 1:
            # if there is more than 1 byte then we received more than one response without getting a callback.
            self.factory.normal = False
            self.transport.loseConnection()
            self.factory.error_value = len(data)
            return
        self.factory.echo_count += 1
        # this calllater should happen immediately as the server side is waiting for 1 second
        reactor.callLater(0, self.gotResponse)
            
    def gotResponse(self):
        print 'Got a response count %s' % self.factory.echo_count
        if self.factory.echo_count >= maxWrites:
            self.factory.normal = True
            self.transport.loseConnection()
            
    def writeData(self):
        print 'SequenceClientProtocol::writeData Write %d data blocks of size %d' % (maxWrites, totalLen)
        for _i in range(0, maxWrites):
            self.transport.write(smallChunk*packet_size)

    def connectionLost(self,reason):
        print 'Connection lost client'
        self.factory.done = 1

class SequenceClientFactory(protocol.ClientFactory):
    def __init__(self):
        self.done = 0
        self.echo_count = 0
        self.normal = False
        self.error_value = 0       

    def buildProtocol(self,addr):
        p = SequenceClientProtocol()
        p.factory = self
        return p


class SequenceTestCase(unittest.TestCase):
    """ Test that the reactor correctly handles IO calls and callLaters's
        Fire 10 packets of 130000 bytes to the server
        The server replies to each packet with a 1 byte acknowledge
        The 'gotResponse' method should be called for each successful ack.
    """

    def testWriter(self):
        print 'Starting'
        f = SequenceServerFactory()
        f.done = 0
        f.problem = 0
        wrappedF = FireOnCloseFactory(f)
        p = reactor.listenTCP(0, wrappedF, interface="127.0.0.1")
        self.addCleanup(p.stopListening)
        n = p.getHost().port
        clientF = SequenceClientFactory()
        wrappedClientF = FireOnCloseFactory(clientF)
        reactor.connectTCP("127.0.0.1", n, wrappedClientF)

        d = defer.gatherResults([wrappedClientF.deferred])
        def check(ignored):
            self.failUnless(clientF.normal,
                            "client received sequence is abnormal %d responses received without processing" % clientF.error_value)
            self.failUnless(clientF.done,
                            "client didn't see connection dropped")
        return d.addCallback(check)

