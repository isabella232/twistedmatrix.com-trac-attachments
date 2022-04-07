import cookielib, cStringIO

from twisted.internet import defer, protocol, reactor
from twisted.web import client, http_headers, iweb



class ResponseBodyHandler(protocol.Protocol):
    def __init__(self, finished):
        self._buffer = cStringIO.StringIO()
        self.finished = finished

    def dataReceived(self, bytes):
        self._buffer.write(bytes)

    def connectionLost(self, reason):
        reason.trap(client.ResponseDone)
        print reason.getErrorMessage()
        if self._buffer is not None:
            b = self._buffer.getvalue()
            self._buffer.close()
            self._buffer = None
            self.finished.callback(b)


def cbResponse(response):
    finished = defer.Deferred()
    response.deliverBody(ResponseBodyHandler(finished))
    return finished


def cbShutdown(result):
    print 'cbShutdown: ' + str(result)
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
        bp = client.FileBodyProducer(cStringIO.StringIO(postdata))

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

    d.addCallback(cbResponse)
    return d


if __name__ == '__main__':
    d = getPage(
        'http://www.twistedmatrix.com/',
        cookies={'foo': 'bar', 'baz': 'blee'},
        followRedirect=True,
        headers={
            'X-BlahBlah': ['foo'],
            'Cookie': ['foosession=fgjkfdjfdkfkd']
        },
        method='GET'
    )
    d.addBoth(cbShutdown)
    reactor.run()
