from twisted.internet import reactor
from twisted.python import log
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, HTTPConnectionPool, RedirectAgent, BrowserLikeRedirectAgent
from twisted.web.iweb import IAgent
from zope.interface import implementer


class IgnoreBody(Protocol):
    def __init__(self, deferred):
        self.deferred = deferred

    def dataReceived(self, bytes):
        pass

    def connectionLost(self, reason):
        self.deferred.callback(None)

@implementer(IAgent)
class NewRedirectAgent(RedirectAgent):

    def _handleRedirect(self, response, method, uri, headers, redirectCount):
        ignore = Deferred()
        response.deliverBody(IgnoreBody(ignore))
        return super(NewRedirectAgent, self)._handleRedirect(response, method, uri, headers, redirectCount)

def cb_request(response):
    print 'Response code:', response.code
    finished = Deferred()
    response.deliverBody(IgnoreBody(finished))
    return finished


pool = HTTPConnectionPool(reactor, persistent=True)
pool.maxPersistentPerHost = 30

pool.retryAutomatically = True
agent = NewRedirectAgent(Agent(reactor, pool=pool))

d = agent.request('GET', 'http://ikea.com/us/en')
d.addCallback(cb_request)
d.addCallback(lambda ignored: reactor.stop())
d.addErrback(log.err)

reactor.run()

