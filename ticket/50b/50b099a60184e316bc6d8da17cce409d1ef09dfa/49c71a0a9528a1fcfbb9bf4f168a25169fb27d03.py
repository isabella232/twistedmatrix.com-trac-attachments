from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor

class ProducerProtocol(Protocol):
    def connectionMade(self):
        print "connection made"
        self.transport.registerProducer(self, True)
        self.transport.loseConnection()

    def stopProducing(self):
        print "Stop producing"

    def connectionLost(self, reason):
        print "connection lost", reason
        reactor.stop()


f = ClientFactory()
f.protocol = ProducerProtocol
reactor.connectTCP("twistedmatrix.com", 80, f)
reactor.run()
