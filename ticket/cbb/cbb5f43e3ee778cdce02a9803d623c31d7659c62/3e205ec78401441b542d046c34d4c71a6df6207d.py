from twisted.application import internet, service, strports
from twisted.web import resource, server



class Main(resource.Resource):
    def getChild(self, name, request):
        if name == '':
            return self

    def render_GET(self, request):
        return request.prePathURL()


root = Main()
site = server.Site(root, logPath='access.log')

application = service.Application('nginx proxy')

addr = 'tcp:8888'
#addr = 'unix:/var/run/twisted-web-host.socket'
strports.service(addr, site).setServiceParent(application)
