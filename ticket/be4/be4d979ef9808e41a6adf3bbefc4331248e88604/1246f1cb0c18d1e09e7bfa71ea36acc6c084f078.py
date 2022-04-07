from twisted.web import server, xmlrpc
from twisted.internet.app import Application

class Echoer(xmlrpc.XMLRPC):

    def test(self):
        return 1

    def _getFunction(self, functionPath):
        return getattr(self, functionPath, None)

application = Application("memleak")
r = Echoer()
server.reactor.listenTCP(2084, server.Site(r))

