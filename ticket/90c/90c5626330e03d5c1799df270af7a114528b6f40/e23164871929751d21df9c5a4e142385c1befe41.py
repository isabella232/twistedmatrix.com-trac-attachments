from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.web.client import getPage
from twisted.web.resource import Resource
from twisted.web.server import Site



class MyResource(Resource):
    """Emulates the service.

    Calls back to the given URL after a little bit of time spent 'processing'.
    """

    isLeaf = True

    PROCESSING_DELAY = 2


    def hit_callback_url(self, url):
        # XXX: Make a request to URL and print the response.
        d = getPage(url)
        def got_page(content):
            print 'Successfully downloaded %s: ' % (url,)
            print content
        def failed_to_get_page(failure):
            print 'COULD NOT DOWNLOAD %s:' % (url,)
            print failure.getTraceback()
        d.addCallbacks(got_page, failed_to_get_page)
        return d


    def render(self, request):
        body = request.content.getvalue()
        reactor.callLater(self.PROCESSING_DELAY, self.hit_callback_url, body)
        return '<html><body>Here I am</body></html>'



def start_web_server():
    endpoint = TCP4ServerEndpoint(reactor, 0)
    root = MyResource()
    site = Site(root)
    d = endpoint.listen(site)
    def web_server_up(listening_port):
        address = listening_port.getHost()
        print 'http://localhost:%s' % (address.port,)
    d.addCallback(web_server_up)
    d.addErrback(disaster)
    return d



def disaster(failure):
    print "GOT UNEXPECTED ERROR"
    print failure.getTraceback()



def main():
    reactor.callWhenRunning(start_web_server)
    reactor.run()



if __name__ == '__main__':
    main()
