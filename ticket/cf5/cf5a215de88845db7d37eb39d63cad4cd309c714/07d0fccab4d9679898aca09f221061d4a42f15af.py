from __future__ import print_function
import treq
from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse
from twisted.cred.portal import IRealm, Portal
from twisted.internet import reactor, defer
from twisted.web import server, resource, guard
from zope.interface import implementer

class GuardedResource(resource.Resource):

    def getChild(self, path, request):
        return self

    def render(self, request):
        return "Authorized"

@implementer(IRealm)
class SimpleRealm(object):

    def requestAvatar(self, avatarId, mind, *interfaces):
        if resource.IResource in interfaces:
            return resource.IResource, GuardedResource(), lambda: None
        raise NotImplementedError()

def main():
    checkers = [InMemoryUsernamePasswordDatabaseDontUse(user='autherized')]
    portal = Portal(SimpleRealm(), checkers)

    resource = guard.HTTPAuthSessionWrapper(portal, [guard.BasicCredentialFactory('auth')])

    @defer.inlineCallbacks
    def send_requests():
        for auth in [('user', 'autherized'), ('user', 'unathorized')]:
            response = yield treq.get('http://localhost:8080', auth=auth)
            content = yield response.text()
            print("response:", response.code, content)

    reactor.callLater(1.0, send_requests)

    reactor.listenTCP(8080, server.Site(resource=resource))
    reactor.run()

if __name__ == '__main__':
    main()
