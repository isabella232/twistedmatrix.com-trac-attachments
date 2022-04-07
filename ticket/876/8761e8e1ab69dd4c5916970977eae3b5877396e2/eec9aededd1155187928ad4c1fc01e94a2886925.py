
import sys

from twisted.internet import reactor
from twisted.internet.defer import Deferred, succeed
from twisted.internet.protocol import Protocol, Factory

from twisted.web import client
from twisted.web.iweb import IBodyProducer, UNKNOWN_LENGTH

from zope.interface import implements


class FastStringProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def stopProducing(self):
        pass

class SlowStringProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = UNKNOWN_LENGTH
        self.func = None

    def startProducing(self, consumer):
        d = Deferred()
        def f():
            consumer.write(self.body)
            d.callback(None)
        self.func = reactor.callLater(3, f)
        return d

    def stopProducing(self):
        if self.func:
            self.func.cancel()

def _test_request(producer):
    agent = client.Agent(reactor)
    d = agent.request('POST', 'http://localhost:8087', bodyProducer=producer("hello"))

    def failure(reason):
        print reason.value
        return reason

    d.addCallback(client.readBody)
    d.addErrback(failure)
    d.addCallback(lambda x: sys.stdout.write(repr(x)+'\n'))

reactor.callLater(1, _test_request, FastStringProducer)
reactor.callLater(4, _test_request, SlowStringProducer)


class Simple(Protocol):
    def connectionMade(self):
        self.transport.write("not http\r\n")
        self.transport.loseConnection()

class SimpleFactory(Factory):
    def buildProtocol(self, addr):
        return Simple()


from twisted.application import internet, service

application = service.Application('test_request')
internet.TCPServer(8087, SimpleFactory()).setServiceParent(application)
