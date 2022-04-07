from twisted.internet import reactor
from twisted.trial import unittest
from twisted.trial.assertions import *
from twisted.trial import util

from twisted.spread import pb
from twisted.cred import portal, checkers, credentials, perspective

from zope.interface import implements

class MyRealm:
    implements(portal.IRealm)
    def requestAvatar(self, avatarId, mind, *interfaces):
        return (perspective.IPerspective, pb.Avatar(), lambda:None)

class ExampleTestCase(unittest.TestCase):
    def setUp(self):
        self.realm = MyRealm()
        portal = pb.Portal(self.realm)
        checker = checkers.InMemoryUsernamePasswordDatabaseDontUse(good='user')
        portal.registerChecker(checker)
        f = pb.PBServerFactory(portal)
        self.port = reactor.listenTCP(0, f, interface="127.0.0.1")
        self.portno = self.port.getHost().port

    def tearDown(self):
        self.connector.disconnect()
        return self.port.stopListening()
    
    def testExample(self):
        f = pb.PBClientFactory()
        d = f.login(credentials.UsernamePassword("bad", "password"), "BRAINS!")
        self.connector = reactor.connectTCP("127.0.0.1", self.portno, f)

        #The Deferred should errback with a Failure (CopiedFailure?) from PB
        #because we used the wrong username/pass

        result = util.wait(d)

        #What does this mean for util.wait? It's supposed to re-raise the
        #original Exception, but how can it know what that was in this case?

        #Presently, this will blow up inside trial as you will see.
