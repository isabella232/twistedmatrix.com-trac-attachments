import sys

from zope.interface import implements

from twisted.python import log
from twisted.internet import reactor
from twisted.web import server, resource, guard
from twisted.cred.portal import IRealm, Portal
from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse

class GuardedResource(resource.Resource):

    def getChild(self, name, request):
        return self

class SimpleRealm(object):
    implements(IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        if resource.IResource in interfaces:
            return resource.IResource, GuardedResource(), lambda: None
        raise NotImplementedError()


def main():
    log.startLogging(sys.stdout)
    checkers = [InMemoryUsernamePasswordDatabaseDontUse(joe='blow')]
    wrapper = guard.HTTPAuthSessionWrapper(
        Portal(SimpleRealm(), checkers),
        [guard.DigestCredentialFactory('md5', 'example.com')])
    reactor.listenTCP(8889, server.Site(resource=wrapper))
    reactor.run()

if __name__ == '__main__':
    main()
