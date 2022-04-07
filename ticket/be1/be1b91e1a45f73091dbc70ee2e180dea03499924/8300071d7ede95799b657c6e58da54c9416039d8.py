from twisted.internet import defer
from twisted.internet import endpoints
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet import threads
from twisted.trial import unittest

class TestServerProtocol(protocol.Protocol):
    def connectionMade(self):
        self.factory.connections += 1
        print '[SERVER] received connection, current count:', self.factory.connections
        if isinstance(self.factory.onConnection, defer.Deferred):
            if not self.factory.onConnection.called:
                self.factory.onConnection.callback(self)

    def connectionLost(self, reason):
        print '[SERVER] connection lost'
        if isinstance(self.factory.onConnectionLost, defer.Deferred):
            if not self.factory.onConnectionLost.called:
                self.factory.onConnectionLost.callback(True)

class TestServerFactory(protocol.Factory):
    protocol = TestServerProtocol
    def __init__(self):
        self.connections = 0
        self.onConnection = None
        self.onConnectionLost = None

class TestClientProtocol(protocol.Protocol):
    def connectionMade(self):
        self.connected = 1
        self.factory.connections += 1
        print '[CLIENT] connection made, number of connections:', self.factory.connections
        if isinstance(self.factory.onConnection, defer.Deferred):
            if not self.factory.onConnection.called:
                self.factory.onConnection.callback(self)
        print '[CLIENT] connection complete'

    def connectionLost(self, reason):
        self.connected = 0
        print '[CLIENT] connection lost, number of connections:', self.factory.connections
        if isinstance(self.factory.onConnectionLost, defer.Deferred):
            if not self.factory.onConnectionLost.called:
                self.factory.onConnectionLost.callback(True)

class TestClientFactory(protocol.ReconnectingClientFactory):
    protocol = TestClientProtocol
    maxDelay = 1
    def __init__(self):
        self.connections = 0
        self.onConnection = None
        self.onConnectionLost = None

class TestBasic(unittest.TestCase):
    def setUp(self):
        self.server = TestServerFactory()
        self.serverPort = reactor.listenTCP(7777, self.server)

    @defer.inlineCallbacks
    def test_reconnect(self):
        self.server.connections = 0
        print
        # connect
        f = TestClientFactory()
        f.onConnection = defer.Deferred()
        self.server.onConnection = defer.Deferred()
        yield reactor.connectTCP('localhost', 7777, f)
        proto = yield f.onConnection
        yield self.server.onConnection
        self.assertEqual(proto.connected, 1)
        self.assertEqual(self.server.connections, 1)

        # force disconnect, wait
        f.onConnectionLost = defer.Deferred()
        f.onConnection = defer.Deferred()
        self.server.onConnectionLost = defer.Deferred()
        proto.transport.loseConnection()
        yield f.onConnectionLost
        yield self.server.onConnectionLost
        self.assertEqual(proto.connected, 0)

        # wait for reconnect
        proto = yield f.onConnection
        self.assertEqual(proto.connected, 1)
        self.assertEqual(self.server.connections, 2)

        # cleanup
        print 'cleaning up...'
        f.continueTrying = 0
        f.onConnectionLost = defer.Deferred()
        self.server.onConnectionLost = defer.Deferred()
        proto.transport.loseConnection()
        yield f.onConnectionLost
        yield self.server.onConnectionLost

    @defer.inlineCallbacks
    def test_reconnect_endpoints(self):
        self.server.connections = 0
        print
        # connect
        f = TestClientFactory()
        endpoint = endpoints.clientFromString(reactor, 'tcp:localhost:7777')
        proto = yield endpoint.connect(f)
        self.assertEqual(proto.connected, 1)
        self.assertEqual(self.server.connections, 1)

        # force disconnect, wait
        f.onConnectionLost = defer.Deferred()
        f.onConnection = defer.Deferred()
        self.server.onConnectionLost = defer.Deferred()
        proto.transport.loseConnection()
        yield f.onConnectionLost
        yield self.server.onConnectionLost

        # wait for reconnect
        proto = yield f.onConnection
        self.assertEqual(proto.connected, 1)
        self.assertEqual(self.server.connections, 2)

        # cleanup
        f.continueTrying = 0
        f.onConnectionLost = defer.Deferred()
        self.server.onConnectionLost = defer.Deferred()
        proto.transport.loseConnection()
        yield f.onConnectionLost
        yield self.server.onConnectionLost

    @defer.inlineCallbacks
    def tearDown(self):
        yield self.serverPort.stopListening()
