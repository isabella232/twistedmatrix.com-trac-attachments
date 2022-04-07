from twisted.internet.epollreactor import install
install()

from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory, ClientFactory, Protocol

class Disconnect(Protocol):
    def connectionMade(self):
        self.transport.pauseProducing()
        reactor.callLater(1, self.transport.getHandle().shutdown, 2)

server = ServerFactory()
server.protocol = Disconnect

class SendWait(Protocol):
    def connectionMade(self):
        # Can't call this synchronously, the transport calls startReading
        # after this returns - oops, that's another bug.
        reactor.callLater(0, self.transport.pauseProducing)
        reactor.callLater(2, self.transport.write, 'x' * 1024 * 1024)
    def connectionLost(self, reason):
        print reason

client = ClientFactory()
client.protocol = SendWait

port = reactor.listenTCP(0, server)
reactor.connectTCP('127.0.0.1', port.getHost().port, client)
reactor.run()
