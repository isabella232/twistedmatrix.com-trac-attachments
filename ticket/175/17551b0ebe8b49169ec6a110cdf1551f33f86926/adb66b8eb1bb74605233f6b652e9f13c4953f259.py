from twisted.trial import unittest
from twisted.web import server, resource
from twisted.internet import protocol, defer, reactor


class C(protocol.Protocol):

    def connectionMade(self):
        self.transport.write("GET / HTTP/1.0\r\n\r\n")
        self.transport.loseConnection()

    def connectionLost(self, reason):
        self.factory.deferred.callback(1)


class R(resource.Resource):

    def render(self, request):
        return "blagoblag"


class TestCL(unittest.TestCase):

    def testCL(self):

        hi_factory = server.Site(R())
        tport = reactor.listenTCP(19999, hi_factory)

        f = protocol.ClientFactory()
        f.protocol = C
        f.deferred = defer.Deferred()
        reactor.connectTCP('localhost', 19999, f)

        def done(r):
            hi_factory.doStop()
            tport.stopListening()
        f.deferred.addCallback(done)

        return f.deferred
