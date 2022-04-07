import gc
from twisted.web import server, xmlrpc
from twisted.internet.app import Application
from twisted.internet import threads

class Echoer(xmlrpc.XMLRPC):

    def test(self):
        return range(10000)

    def render(self, request):
        gc.collect()
        print gc.garbage
        request.content.seek(0, 0)

	d = threads.deferToThread( self.test )
        d.addErrback( self._ebRender )
        d.addCallback( self._cbRender, request )
        return server.NOT_DONE_YET

    def _getFunction(self, functionPath):
        return getattr(self, functionPath, None)

application = Application("memleak")
r = Echoer()
server.reactor.listenTCP(2084, server.Site(r))
