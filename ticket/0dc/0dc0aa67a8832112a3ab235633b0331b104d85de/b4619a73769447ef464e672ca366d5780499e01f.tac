from twisted.web import server, resource, static
from twisted.application import internet, service

r = static.Data('test\xff', u'image/x-icon')

root = resource.Resource()
root.putChild('foo', r)

print static.__file__

application = service.Application("Bug Demo")
internet.TCPServer(8080, server.Site(root)).setServiceParent(application)
