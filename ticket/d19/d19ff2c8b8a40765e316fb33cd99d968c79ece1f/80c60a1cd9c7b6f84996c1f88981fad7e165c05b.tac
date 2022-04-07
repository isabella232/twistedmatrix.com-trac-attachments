from zope.interface import implements

from twisted.application import internet, service
from twisted.web import http, server, resource, guard
from twisted.internet import reactor, ssl, defer

from twisted.cred.portal import Portal, IRealm
from twisted.cred.checkers import ICredentialsChecker, \
    InMemoryUsernamePasswordDatabaseDontUse
from twisted.cred.credentials import IUsernamePassword

HTTP_PORT     = 9090

class V1(resource.Resource):
    isLeaf = True
    
    def __init__(self):
        resource.Resource.__init__(self)

        self.putChild("", self)

    def render_GET(self, request):
        return 'Hello!'

class Root(resource.Resource):

    def __init__(self):
        resource.Resource.__init__(self)

        self.putChild("1", V1())
        # need to do this for resources at the root of the site such as ?describe
        self.putChild("", self)
    
    def render_GET(self, request):
        request.setResponseCode(http.NOT_IMPLEMENTED)
        return http.RESPONSES[http.NOT_IMPLEMENTED]


class MyRealm(object):
    """
    A realm which gives out L{Resource} instances for authenticated users.
    """
    implements(IRealm)

    def __init__(self, resource):
        self.resource = resource

    def requestAvatar(self, avatarId, mind, *interfaces):
        from twisted.python import log
        #log.msg(self.__class__.__name__,'requestAvatar', self.resource, avatarId, mind, interfaces )

        if resource.IResource in interfaces:
            return resource.IResource, self.resource, lambda: None
        raise NotImplementedError()
    

checker = InMemoryUsernamePasswordDatabaseDontUse()
checker.addUser("guest", "password")

svc = service.MultiService()

site = server.Site( guard.HTTPAuthSessionWrapper(Portal(MyRealm(Root()),
                      [checker]),
                      [guard.BasicCredentialFactory('test realm')]))

internet.TCPServer(HTTP_PORT, site).setServiceParent(svc)

application = service.Application("isi_api_d")

svc.setServiceParent(application)


