
# Copyright (c) 2001-2006 Twisted Matrix Laboratories.
# See LICENSE for details.
import sys
from zope.interface import implements
from twisted.internet import iocpreactor
iocpreactor.install()

from twisted.spread import pb
from twisted.cred.portal import IRealm

class SimplePerspective(pb.Avatar):

    def perspective_echo(self, text):
        print 'echoing',text
        return text

    def perspective_transfer(self, data, msg):
        print 'Transfer', data['description'], msg
        print 'Samples ', len(data['values'])
        return msg

    def logout(self):
        print self, "logged out"
        reactor.callLater(10, reactor.stop)


class SimpleRealm:
    implements(IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        if pb.IPerspective in interfaces:
            avatar = SimplePerspective()

            return pb.IPerspective, avatar, avatar.logout 
        else:
            raise NotImplementedError("no interface")

class MyPBFactory(pb.PBServerFactory):
    
    def __init__(self, root):
        pb.PBServerFactory.__init__(self, root)

    def clientConnectionMade(self, broker):        
        broker.transport.setTcpNoDelay(1)
        
if __name__ == '__main__':
    from twisted.internet import reactor
    from twisted.cred.portal import Portal
    from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse
    portal = Portal(SimpleRealm())
    checker = InMemoryUsernamePasswordDatabaseDontUse()
    checker.addUser("guest", "guest")
    portal.registerChecker(checker)
    reactor.listenTCP(pb.portno, MyPBFactory(portal))
    reactor.run()
