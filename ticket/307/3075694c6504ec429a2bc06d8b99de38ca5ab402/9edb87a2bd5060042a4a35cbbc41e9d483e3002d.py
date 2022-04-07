from twisted.internet import reactor, stdio, protocol, interfaces
from zope.interface import implements
import sys

class MyProto(protocol.Protocol):
    implements(interfaces.IHalfCloseableProtocol)

    def connectionMade(self):
        sys.stderr.write('connectionMade\n')
        self.send(0)

    def readConnectionLost(self):
        sys.stderr.write('readConnectionLost\n')

    def writeConnectionLost(self):
        sys.stderr.write('writeConnectionLost\n')
        self.loseConnection()

    def connectionLost(self, reason):
        sys.stderr.write('connectionLost\n')

    def send(self, num):
        if num < 10:
            self.transport.write(str(num) + '\n')
            reactor.callLater(0.1, self.send, num+1)
        else:
            self.transport.write('DONE\n')
            reactor.callLater(0.1, reactor.stop)

def main():
    s = stdio.StandardIO(MyProto())
    #s._writer.enableReadHack = False
    reactor.run()
    sys.stderr.write('exiting\n')

if __name__ == '__main__':
    main()
