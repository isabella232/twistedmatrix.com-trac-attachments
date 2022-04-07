from twisted.internet import defer, reactor as mod_reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.protocols.policies import (
    ProtocolWrapper,
    WrappingFactory,
    )
from twisted.web.client import getPage
from twisted.web.resource import Resource
from twisted.web.server import Site



class CallbackResource(Resource):
    """A Twisted web resource that waits for a JSON post."""


    def __init__(self, on_post):
        """A web resource that fires a Deferred on POST.

        :param on_post: A function that will be called when a POST request is
            received. Will be fired with a tuple containing the request method
            and body.
        """
        Resource.__init__(self)
        self.on_post = on_post


    def render(self, request):
        # The first request to this resource will be treated as the actual
        # callback request.
        method = request.method
        body = request.content.getvalue()
        # XXX: By calling this now we trigger the shut down and the response
        # is never sent.  Want to be able to schedule the call to 'on_post'
        # for *after* the response is sent.
        self.on_post((method, body))
        return '<html></html>'



class NotifyOnConnectionLost(ProtocolWrapper):

    def __init__(self, factory, wrappedProtocol):
        ProtocolWrapper.__init__(self, factory, wrappedProtocol)
        self.connectionLostDeferred = defer.Deferred()


    def connectionLost(self, reason):
        ProtocolWrapper.connectionLost(self, reason)
        if self.connectionLostDeferred:
            d, self.connectionLostDeferred = self.connectionLostDeferred, None
            d.callback(None)



class DisconnectAllOnStopListening(WrappingFactory):

    protocol = NotifyOnConnectionLost


    def __init__(self, disconnectedDeferred, wrappedFactory):
        WrappingFactory.__init__(self, wrappedFactory)
        self.disconnectedDeferred = disconnectedDeferred


    def doStop(self):
        WrappingFactory.doStop(self)
        d = defer.gatherResults(
            [p.connectionLostDeferred for p in self.protocols])
        d.chainDeferred(self.disconnectedDeferred)



class WebServer(object):

    def __init__(self, service_root, reactor):
        self.service_root = service_root
        self.reactor = reactor
        self._clear_state()


    def _clear_state(self, passthrough=None):
        self._disconnected = None
        self._listening_port = None
        self._on_callback = None
        return passthrough


    def _run_web_server(self, root):
        endpoint = TCP4ServerEndpoint(self.reactor, 0)
        self._disconnected = defer.Deferred()
        site = DisconnectAllOnStopListening(self._disconnected, Site(root))
        d = endpoint.listen(site)
        def web_server_up(listening_port):
            self._listening_port = listening_port
            address = listening_port.getHost()
            return 'http://localhost:%s' % (address.port,)
        return d.addCallback(web_server_up)


    def make_root_resource(self, deferred):
        root = Resource()
        root.putChild('callback', CallbackResource(deferred.callback))
        return root


    def run_web_server(self):
        self._on_callback = defer.Deferred()
        root = self.make_root_resource(self._on_callback)
        return self._run_web_server(root)


    def shut_down_web_server(self, passthrough=None):
        d = self._listening_port.stopListening()
        # We are only properly shut down when the port has stopped
        # listening and when all the clients have disconnected.
        d = defer.gatherResults([self._disconnected, d])
        return d.addCallback(lambda x: self._clear_state(passthrough))


    def send_api_request(self, url):
        # XXX: In our real code, this is actually a blocking API call, and we
        # don't care about the response content in the happy case.
        callback_url = '%s/callback' % (url,)
        d = getPage(self.service_root, method='POST', postdata=callback_url)
        def sent_request(content):
            print 'Sent API request to %s' % (self.service_root,)
            print content
            print
            print 'Waiting for callback'
            return self._on_callback
        return d.addCallback(sent_request)


    def run(self):
        d = self.run_web_server()
        d.addCallback(self.send_api_request)
        return d



def main(service_root):

    webserver = WebServer(service_root, mod_reactor)

    def got_response(response):
        print 'Got successful response: %r' % (response,)

    def disaster(error):
        print "UNEXPECTED ERROR\n"
        print error.getTraceback()

    def send_request():
        d = webserver.run()
        d.addCallback(got_response)
        d.addErrback(disaster)
        d.addBoth(lambda x: mod_reactor.stop())
        return d

    mod_reactor.callWhenRunning(send_request)
    mod_reactor.run()



if __name__ == '__main__':
    import sys
    main(sys.argv[1])
