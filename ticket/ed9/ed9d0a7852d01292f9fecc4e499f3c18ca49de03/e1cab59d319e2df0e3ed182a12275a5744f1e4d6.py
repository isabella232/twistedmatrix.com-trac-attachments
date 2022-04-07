from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import HostnameEndpoint
from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import react

class F(Factory):
    protocol = Protocol

@inlineCallbacks
def go(reactor):
    ep = HostnameEndpoint(reactor, "twistedmatrix.com", 443)
    d = ep.connect(F())
    d.cancel()
    yield d

react(go, ())
