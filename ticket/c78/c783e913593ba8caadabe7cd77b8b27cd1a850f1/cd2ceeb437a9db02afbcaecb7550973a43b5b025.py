from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor

class Disconnecter(Protocol):
	def connectionMade(self):
		self.transport.write("x")
		self.transport.loseConnection()

        def connectionLost(self, reason):
                print "lost connection", reason


factory = ClientFactory()
factory.protocol = Disconnecter

from sys import argv
reactor.connectTCP("127.0.0.1", int(argv[1]), factory)
reactor.run()
