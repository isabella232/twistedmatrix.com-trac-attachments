import time

from twisted.internet import reactor, defer, ssl
from twisted.internet.protocol import Protocol, ServerFactory
from twisted.web.client import HTTPClientFactory

class TimeoutProtocol(Protocol):
    """A really dumb protocol which does nothing for 60 seconds, then
       terminates the connection"""
    def connectionMade(self):
        reactor.callLater(60, self.transport.loseConnection)

class TimeoutServerFactory(ServerFactory):
    """Protocol factory for TimeoutProtocol"""
    protocol = TimeoutProtocol

@defer.inlineCallbacks
def run():
    # listen on some port with our dumb TimeoutProtocol
    sock = reactor.listenTCP(0, TimeoutServerFactory())
    port = sock.getHost().port

    # first, try plain HTTP request
    start_time = time.time()
    f = HTTPClientFactory('http://127.0.0.1:%u/' % port, timeout=2)
    reactor.connectTCP('localhost', port, f, timeout=2)
    try:
        r = yield f.deferred
        print "HTTP Request Done:", r
    except Exception, e:
        print "HTTP Request Failed:", e
    print "Duration:", time.time() - start_time

    # next, try HTTPS request
    start_time = time.time()
    f = HTTPClientFactory('https://127.0.0.1:%u/' % port, timeout=2)
    ctx = ssl.ClientContextFactory()
    reactor.connectSSL('localhost', port, f, ctx, timeout=2)
    try:
        r = yield f.deferred
        print "HTTP Request Done:", r
    except Exception, e:
        print "HTTP Request Failed:", e

    print "Duration:", time.time() - start_time

    # done, quit
    reactor.stop()

reactor.callWhenRunning(run)
reactor.run()
