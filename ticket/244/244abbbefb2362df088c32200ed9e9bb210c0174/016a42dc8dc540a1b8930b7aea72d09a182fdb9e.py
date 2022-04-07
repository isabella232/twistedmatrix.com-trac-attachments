import sys

from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.protocol import Protocol, ReconnectingClientFactory
from twisted.python import log


class DumbProtocol(Protocol):

    def connectionMade(self):
        print 'Connection made.'
        from twisted.internet import reactor
        reactor.callLater(2, self.transport.loseConnection)

class Factory(ReconnectingClientFactory):
    protocol = DumbProtocol


def connected(res):
    log.msg('connected')

def connect(port):
    from twisted.internet import reactor
    endpoint = TCP4ClientEndpoint(reactor, 'localhost', port)
    d = endpoint.connect(Factory())
    d.addCallback(connected)

def connect2(port):
    from twisted.internet import reactor
    reactor.connectTCP('localhost', port, Factory())

def main():
    log.startLogging(sys.stdout)
    from twisted.internet import reactor
    reactor.callWhenRunning(connect2, int(sys.argv[1]))
    reactor.run()

if __name__ == '__main__':
    main()
