#!/usr/bin/env python
# -*- coding: utf-8 -*-

from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory, ClientFactory, Protocol

state = dict()

class FakeProducer(object):
	def resumeProducing(self):
		print "resumeProducing"
	def pauseProducing(self):
		print "pauseProducing"
	def stopProducing(self):
		print "stopProducing"

class A(Protocol):
	def connectionMade(self):
		state[self.__class__.__name__] = self
		if len(state) == 2:
			start()
	def connectionLost(self, reason):
		print self.__class__.__name__, "disconnected"

class B(A):
	pass

def start():
	state["Aproducer"] = FakeProducer()
	state["A"].transport.registerProducer(state["Aproducer"], True)
	state["A"].transport.write("a" * (2**16 +1))
	state["A"].transport.stopProducing()
	reactor.callLater(0.1, stop)

def stop():
	state["A"].transport.unregisterProducer()
	state["B"].transport.loseConnection()

class AFactory(ServerFactory):
	protocol = A
class BFactory(ClientFactory):
	protocol = B

if __name__ == "__main__":
	reactor.listenTCP(8080, AFactory())
	reactor.callWhenRunning(reactor.connectTCP, "127.0.0.1", 8080, BFactory())
	reactor.run()
