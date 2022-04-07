import cookielib

from twisted.internet import defer, protocol, reactor

from twisted.web import client, http_headers, iweb

from zope.interface import implements



class RequestBodyProducer(object):
    implements(iweb.IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return defer.succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


class ResponseBodyPrinter(protocol.Protocol):
    def __init__(self, finished):
        self.finished = finished
        self.remaining = 1024 * 10

    def dataReceived(self, bytes):
        if self.remaining:
            display = bytes[:self.remaining]
            print 'Some data received:'
            print display
            self.remaining -= len(display)

    def connectionLost(self, reason):
        print 'Finished receiving body:', reason.getErrorMessage()
        self.finished.callback(None)


def cbResponse(response):
    print response.version, response.code, response.phrase
    print list(response.headers.getAllRawHeaders())
    finished = defer.Deferred()
    response.deliverBody(ResponseBodyPrinter(finished))
    return finished


def cbShutdown(ignored):
    print ignored
    reactor.stop()


def getPage(
    url,
    afterFoundGet=False,
    agent="Twisted PageGetter",
    contextFactory=None,
    cookies=None,
    followRedirect=False,
    headers=None,
    method='GET',
    postdata=None,
    redirectLimit=20,
    timeout=0
):
    """
    Download a web page as a string.

    Download a page. Return a deferred, which will callback with a
    page (as a string) or errback with a description of the error.
    """

    headers = http_headers.Headers(rawHeaders=headers)
    if cookies is not None:
        for cookie, cookval in cookies.items():
            headers.addRawHeader('Cookie', '%s=%s' % (cookie, cookval))

    bp = None
    if postdata is not None:
        bp = RequestBodyProducer(postdata)

    if contextFactory is not None:
        a = client.Agent(reactor, contextFactory=contextFactory)
    else:
        a = client.Agent(reactor)

    c = client.CookieAgent(a, cookielib.CookieJar())
    if not followRedirect:
        d = c.request(method, url, headers=headers, bodyProducer=bp)
    else:
        r = client.RedirectAgent(c, redirectLimit=redirectLimit)
        d = r.request(method, url, headers=headers, bodyProducer=bp)

    return d


if __name__ == '__main__':
    d = getPage(
        'http://www.twistedmatrix.com',
        cookies={'foo': 'bar', 'baz': 'blee'},
        headers={
            'X-BlahBlah': ['foo'],
            'Cookie': ['foosession=fgjkfdjfdkfkd']
        },
        method='GET'
    )
    d.addCallback(cbResponse)
    d.addBoth(cbShutdown)
    reactor.run()
