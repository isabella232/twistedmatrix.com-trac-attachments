from twisted.python import log
from twisted.web import client
from twisted.internet import reactor, defer, protocol

class BuggyProtocol(protocol.Protocol):

    def dataReceived(self, data):
        1 / 0

    def connectionLost(self, reason):
        if reason.check(client.ResponseDone):
            self.done.callback(None)
        else:
            self.done.errback(reason)

protocol = BuggyProtocol()
protocol.done = defer.Deferred()

agent = client.Agent(reactor, client.WebClientContextFactory())
d = agent.request("GET", "http://localhost:8000/")

def got_response(r):
    r.deliverBody(protocol)
    return protocol.done

d.addCallback(got_response)
d.addErrback(log.err)
d.addBoth(lambda _: reactor.stop())
reactor.run()
