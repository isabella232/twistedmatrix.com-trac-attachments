import os, sys, time

from twisted.internet import defer, reactor, stdio, interfaces
from twisted.protocols import basic
from twisted.python import usage
from zope.interface import implements

class TestReader (basic.LineReceiver):
    from os import linesep as delimiter
    implements(interfaces.IHalfCloseableProtocol)

    def __init__ (self):
        pass

    def lineReceived (self, line):
        self.transport.write(line + "\n")

    def stop (self):
        print >>sys.stderr, "stop"
        self.transport.loseConnection()

    def readConnectionLost (self):
        print >>sys.stderr, "readConnectionLost"
        reactor.callLater(1, self.transport.write, "stopping\n")
        reactor.callLater(2, self.stop)

    def writeConnectionLost(self):
        print >>sys.stderr, "writeConnectionLost"
        pass

    def connectionLost(self, reason):
        print >>sys.stderr, "connectionLost"
        reactor.callWhenRunning(reactor.stop)

stdio.StandardIO(TestReader())
reactor.run()
 