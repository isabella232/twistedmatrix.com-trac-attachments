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
    
         root = Resource()
         root.isLeaf = False

         foo = Resource()
         foo.isLeaf = False
         
         die = Die()
         foo.putChild("die", die)
  
         root.putChild("foo", foo)

        
         return resource.IResource, root, lambda: None
      raise NotImplementedError()


if __name__ == "__main__":
   log.startLogging(sys.stdout)


   # set up /foo/die
   checker = [InMemoryUsernamePasswordDatabaseDontUse(foo='bar')]
   wrapper = guard.HTTPAuthSessionWrapper(Portal(SimpleRealm(), checker),
                                         [guard.BasicCredentialFactory("/foo/die")])

   reactor.listenTCP(9999, server.Site(wrapper))
   reactor.run()

