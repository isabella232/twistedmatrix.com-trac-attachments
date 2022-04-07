#from twisted.internet.iocpreactor import install
#install()
from twisted.internet import reactor, protocol
from twisted.internet.protocol import ServerFactory, ClientFactory, Protocol

from twisted.python import log

import sys

log.startLogging(sys.stdout, True)

class FailProto(Protocol):
    def connectionMade(self):
        reactor.callLater(1, lambda: cf.proto.transport.write('megafail!'))
        reactor.callLater(2, lambda: cf.proto.transport.write('megafail2'))

    def dataReceived(self, data):
        print 'dR', data
        self.transport.pauseProducing()
        reactor.callLater(3, self.transport.resumeProducing)

class FailFactory(ClientFactory):
    def buildProtocol(self, addr):
        self.proto = Protocol()
        return self.proto

cf = FailFactory()
sf = ServerFactory()
sf.protocol = FailProto

reactor.listenTCP(9090, sf)
reactor.connectTCP('127.0.0.1', 9090, cf)
reactor.run()

