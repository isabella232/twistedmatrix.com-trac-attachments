from twisted.internet import reactor
from twisted.internet.protocol import Factory, ClientCreator
from twisted.protocols import amp
from twisted.trial import unittest



class SomeError(Exception):
	pass


class SomeCommand(amp.Command):
	errors = { SomeError: 'SOME_ERROR' }


class AnotherCommand(SomeCommand):
	pass


class SomeProtocol(amp.AMP):

	@SomeCommand.responder
	def command1(self):
		raise SomeError()

	@AnotherCommand.responder
	def command2(self):
		raise SomeError()


class AmpTestCase(unittest.TestCase):

	def setUp(self):
		self.port = 5555
		f = Factory()
		f.protocol = SomeProtocol
		self.iport = reactor.listenTCP(self.port, f)
		self.proto = None


	def tearDown(self):
		self.iport.stopListening()
		if self.proto is not None:
			return self.proto.transport.loseConnection()


	def testErrorPropagation(self):
		def gotError(error):
			self.failUnlessRaises(SomeError, error.raiseException)

		def connected(proto):
			self.proto = proto
			d = proto.callRemote(AnotherCommand)
			d.addCallback(lambda _ : self.fail('Should have failed'))
			d.addErrback(gotError)
			return d

		client = ClientCreator(reactor, amp.AMP)
		d = client.connectTCP('localhost', self.port)
		d.addCallback(connected)
		return d

