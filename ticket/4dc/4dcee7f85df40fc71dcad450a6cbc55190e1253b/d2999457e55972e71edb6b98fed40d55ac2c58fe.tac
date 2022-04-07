from twisted.application import service
from twisted.application import internet
from twisted.web import resource, server

class Simple(resource.Resource):
    isLeaf = True

    def render_GET(self, request):
        return '<html><head><title>Foo</title></head><body>Foo</body></html>'

application = service.Application("simple")
internet.TCPServer(
    8080,
    server.Site(
        Simple()
    )
).setServiceParent(application)
