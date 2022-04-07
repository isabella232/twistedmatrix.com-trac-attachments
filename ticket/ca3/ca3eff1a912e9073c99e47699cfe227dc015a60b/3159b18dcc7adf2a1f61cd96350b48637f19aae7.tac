from twisted.web.server import Site, NOT_DONE_YET
from twisted.web.resource import Resource

class Duh(Resource):
    def render(self, request):
    	request.write(u'wut')
	request.finish()
	return NOT_DONE_YET

duh = Duh()
duh.putChild("", Duh())

site = Site(duh)


from twisted.application.internet import TCPServer
from twisted.application.service import Application

application = Application("web-sux")
TCPServer(8081, site).setServiceParent(application)
