import sys

from twisted.internet.epollreactor import install
install()

from twisted.python import log
from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator, Protocol
from twisted.internet.defer import Deferred, gatherResults
from twisted.internet.task import coiterate

class Client(Protocol):
    counter = 0
    outstandingConnects = 0
    mostEver = 0

    def __init__(self):
        self.lost = Deferred()

    def connectionMade(self):
        self.lost.callback(None)
        if Client.outstandingConnects > Client.mostEver:
            print 'Most ever outstanding connects:', Client.outstandingConnects
            Client.mostEver = Client.outstandingConnects

        Client.outstandingConnects -= 1
        Client.counter += 1
        if Client.counter % 1000 == 0:
            print 'Connected', Client.counter, Client.outstandingConnects
        
        self.transport.write('GET / HTTP/1.1\r\n\r\n')


def main(host, port, total, concurrent):
    cc = ClientCreator(reactor, Client)
    def f():
        for n in xrange(total):
            Client.outstandingConnects += 1
            ip = '127.%d' % (n % 256,)
            d = cc.connectTCP(host, port, bindAddress=(ip, 0))
            d.addCallback(lambda proto: proto.lost)
            yield d
    g = f()
    d = gatherResults([coiterate(g) for n in range(concurrent)])
    d.addErrback(log.err)
    d.addCallback(lambda ign: reactor.stop())
    reactor.run()

log.startLogging(sys.stdout)
main('127.0.0.1', 2000, 100000, 100)
