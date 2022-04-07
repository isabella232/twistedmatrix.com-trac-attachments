from twisted.trial import unittest

from twisted.internet import protocol, defer, reactor


class ProducerProtocol(protocol.Protocol):

    def __init__(self):
        self.deferred = defer.Deferred()

    def connectionMade(self):
        self.transport.registerProducer(self, True)
        self.transport.loseConnection()

    def resumeProducing(self):
        pass

    def pauseProducing(self):
        pass

    def stopProducing(self):
        self.stopProducingCalled = True

    def connectionLost(self, reason):
        self.deferred.callback(None)


class ProducerTest(unittest.TestCase):

    def test_connectionNotLostUntilProducerDone(self):
        """
        Run forever (or until timeout), because we loseConnection() without
        unregistering producer. Except - BUG! It does disconnect.
        """
        sf = protocol.Factory()
        sf.protocol = protocol.Protocol
        port = reactor.listenTCP(0, sf)
        self.addCleanup(port.stopListening)

        p = ProducerProtocol()
        f = protocol.ClientFactory()
        f.buildProtocol = lambda addr: p
        reactor.connectTCP("localhost", port.getHost().port, f)
        return p.deferred
