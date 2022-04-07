

import socket

from twisted.trial import unittest
from twisted.internet import endpoints, protocol


class TestFactory(protocol.Factory):

    def buildProtocol(self, addr):
        raise Exception('we should not get this far')


class HorribleTest(unittest.TestCase):

    def test_TCP4ClientConnectionCancelled(self):
        # Create an actual socket (listening on loopback) to test against.
        # We are never going to accept connection attempts on it.
        sock = socket.socket()
        sock.bind(('127.0.0.1', 0))
        sock.listen(1)
        self.addCleanup(sock.close)

        localhost, port = sock.getsockname()

        from twisted.internet import reactor

        ep = endpoints.TCP4ClientEndpoint(reactor, localhost, port)

        factory = TestFactory()

        d = ep.connect(factory)

        d.cancel()

        return self.assertFailure(d, error.ConnectingCancelledError)
