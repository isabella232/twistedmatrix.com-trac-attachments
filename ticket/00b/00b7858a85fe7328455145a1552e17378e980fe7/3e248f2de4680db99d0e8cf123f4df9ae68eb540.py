from twisted.internet.protocol import Protocol, ClientFactory
import sys
import string

class Spew(Protocol):
    def connectionMade(self):
        self.d = ''.join(string.digits) * 1000
        reactor.callLater(0, self.write)

    def write(self):
        if self.d:
            self.transport.write(self.d)
            reactor.callLater(0, self.write)

    def connectionLost(self, reason):
        self.d = None
        sys.stdout.write("\n")
    
    def dataReceived(self, data):
        sys.stdout.write(data)

class SpewClientFactory(ClientFactory):
    def startedConnecting(self, connector):
        print 'Started to connect.'
    
    def buildProtocol(self, addr):
        print 'Connected.'
        return Spew()
    
    def clientConnectionLost(self, connector, reason):
        print 'Lost connection.  Reason:', reason
        reactor.stop()
    
    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason
        reactor.stop()

from twisted.internet import reactor
reactor.connectTCP('localhost', 8007, SpewClientFactory())
reactor.run()
