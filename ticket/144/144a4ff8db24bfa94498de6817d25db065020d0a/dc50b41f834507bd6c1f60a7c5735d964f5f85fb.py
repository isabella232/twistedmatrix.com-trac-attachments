from zope.interface import implements
from twisted.internet import reactor
from twisted.web.resource import IResource, Resource
from twisted.web import server, guard
from twisted.cred.portal import IRealm
from twisted.python import log

import sys

from zope.interface import implements

from twisted.python import log
from twisted.internet import reactor
from twisted.web import server, resource, guard
from twisted.cred.portal import IRealm, Portal
from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse



class Die(Resource):
   isLeaf = True
   def render_GET(self, request):
      reactor.stop()
      return ""   # avoid unhandled error

class SimpleRealm(object):
   implements(IRealm)

   def requestAvatar(self, avatarId, mind, *interfaces):
      if resource.IResource in interfaces:
         return resource.IResource, Die(), lambda: None
      raise NotImplementedError()


if __name__ == "__main__":
   log.startLogging(sys.stdout)


   # set up /1/die
   checker1 = [InMemoryUsernamePasswordDatabaseDontUse(foo='bar')]
   dieNodeWrapper1 = guard.HTTPAuthSessionWrapper(Portal(SimpleRealm(), checker1),
                                         [guard.BasicCredentialFactory("/1/die")])
   dieResource1 = Resource()
   dieResource1.putChild("die", dieNodeWrapper1)

 
   # set up /2/die
   checker2 = [InMemoryUsernamePasswordDatabaseDontUse(baz='bat')]
   dieNodeWrapper2 = guard.HTTPAuthSessionWrapper(Portal(SimpleRealm(), checker2),
                                         [guard.BasicCredentialFactory("/2/die")])
   dieResource2 = Resource()
   dieResource2.putChild("die", dieNodeWrapper2)


   root = Resource()
   root.putChild("1", dieResource1)
   root.putChild("2", dieResource2)

   reactor.listenTCP(9999, server.Site(root))
   reactor.run()

