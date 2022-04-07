from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET, Site
from twisted.internet import reactor
from twisted.python.log import startLogging
from sys import stdout

class BrokenResource(Resource):
    def getChild(self, name, request):
        return self

    def render_GET(self, request):
        reactor.callLater(3, request.finish)
        request.channel.transport.loseConnection()
        return NOT_DONE_YET

startLogging(stdout)
reactor.listenTCP(8088, Site(BrokenResource()))
reactor.run()
