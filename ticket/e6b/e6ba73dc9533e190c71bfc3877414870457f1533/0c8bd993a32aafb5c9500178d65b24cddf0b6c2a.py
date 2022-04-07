#!/usr/bin/python
import twisted.web.proxy, twisted.internet.reactor, twisted.web.resource
import twisted.web.client, twisted.web.static, twisted.copyright, urlparse
from twisted.web.proxy import ProxyClientFactory
from twisted.web import server
from twisted.internet import reactor

def hostport(host, port, defaultport=80):
    if port == defaultport: return host
    return '%s:%d' % (host, port)

# default, for when the class below doesn't exist
ReverseProxyResource = twisted.web.proxy.ReverseProxyResource

# rename this subclass to see the test fail
class ReverseProxyResource(twisted.web.proxy.ReverseProxyResource):
    def render(self, request):
        request.received_headers['host'] = hostport(self.host, self.port)
        request.content.seek(0, 0)
        qs = urlparse.urlparse(request.uri)[4]
        if qs:
            rest = self.path + '?' + qs
        else:
            rest = self.path
        clientFactory = ProxyClientFactory(request.method, rest, 
                                     request.clientproto, 
                                     request.getAllHeaders(),
                                     request.content.read(),
                                     request)
        reactor.connectTCP(self.host, self.port, clientFactory)
        return server.NOT_DONE_YET

### testing
def ok(a, b): assert a == b, (a, b)

testport = 7200

def test_host_header():
    """Ensure port number included in host header.
    
    http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.23
        A "host" without any trailing port information implies the
        default port for the service requested (e.g., "80" for an
        HTTP URL).

    Thus the port number must be included if it's not the default.  If
    it is the default, it's OK to either include it or not, but I'm
    not testing that case.
    
    """

    print twisted.copyright.version

    # set up front end server
    rpr = ReverseProxyResource('localhost', testport, '/proxied')
    proxyroot = twisted.web.resource.Resource()
    proxyroot.putChild('proxied', rpr)
    twisted.internet.reactor.listenTCP(testport+1, twisted.web.server.Site(proxyroot))

    # set up backend server
    class host_header_getter(twisted.web.static.Data):
        def render(self, request):
            self.last_host_header = request.getHeader("host")
            return twisted.web.static.Data.render(self, request)
    proxied_resource = host_header_getter('<b>yes</b>', 'text/html')
    root = twisted.web.resource.Resource()
    root.putChild('proxied', proxied_resource)
    twisted.internet.reactor.listenTCP(testport, twisted.web.server.Site(root))

    # issue request
    req = twisted.web.client.getPage('http://localhost:%d/proxied' % (testport+1))
    def receivePage(page_contents):
        twisted.internet.reactor.stop()
        ok(page_contents, '<b>yes</b>')
        ok(proxied_resource.last_host_header, 'localhost:%d' % testport)
    req.addCallback(receivePage)

    errors = []
    def fail(err_description):
        errors.append(err_description)
        twisted.internet.reactor.stop()
        return err_description
    req.addErrback(fail)

    # run
    twisted.internet.reactor.run()

    # check for success
    if errors != []:
        for error in errors:
            print error
        assert 0

if __name__ == '__main__': test_host_header()

