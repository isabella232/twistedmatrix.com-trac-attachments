from twisted.internet.win32eventreactor import install
install()

from twisted.internet.protocol import Protocol, ServerFactory
from twisted.internet import reactor

class SomeProto(Protocol):
	def connectionMade(self):
		print "connection made"

	def dataReceived(self, data):
		print "data received", repr(data)

	def connectionLost(self, reason):
		print "connection lost", reason

factory = ServerFactory()
factory.protocol = SomeProto

print reactor.listenTCP(0, factory).getHost().port
reactor.run()
