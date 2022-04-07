from twisted.internet import reactor, defer, protocol
from twisted.trial import unittest
from twisted.trial.assertions import *
from twisted.trial import util

from twisted.spread import pb
from twisted.cred import portal, checkers, credentials, perspective

from zope.interface import implements
"""
I think trial should show roughly similar output for text_example1
and test_example2. They both leave selectables in the reactor, thus they
should both cause "cleanup errors" warnings (and they do).

They both also return None (which indicates a passing test).

test_example1 gets [ERROR], and you see this at the end of trials output:
===============================================================================
[ERROR]: test_example1 (test_example.Example1TestCase)


Failure: twisted.cred.error.UnauthorizedLogin: 
-------------------------------------------------------------------------------
Ran 2 tests in 1.085s

FAILED (errors=1, successes=1)

But! test_example2 gets [OK]

So, what's the difference? They both leave cleanup errors, so even if they
return None from the test method, they should still be shown as [ERROR], Right?

Also, why is "Failure: twisted.cred.error.UnauthorizedLogin" being reported as
shown above? How is trial even getting a hold of it considering that I trapped
it with deferredError?

Also, the textual format of the above error output leads me to expect a
traceback to be shown. Of course there is no traceback. This is confusing.
"""

class Example1_TestCase(unittest.TestCase):
    def test_example1(self):
        #PB Server
        self.realm = MyRealm()
        portal = pb.Portal(self.realm)
        checker = checkers.InMemoryUsernamePasswordDatabaseDontUse(good='user')
        portal.registerChecker(checker)
        f = pb.PBServerFactory(portal)
        self.port = reactor.listenTCP(0, f, interface="127.0.0.1")
        self.portno = self.port.getHost().port

        # PB Client
        f = pb.PBClientFactory()
        d = f.login(credentials.UsernamePassword("bad", "password"), "BRAINS!")
        self.connector = reactor.connectTCP("127.0.0.1", self.portno, f)

        failure = util.deferredError(d)
        assertEquals(failure.type, "twisted.cred.error.UnauthorizedLogin")

        # if you see this, then it means that this test passed.
        print "\nRETURNING None FROM TEST METHOD"

class Example2_TestCase(unittest.TestCase):
    def setUp(self):
        # lets leave a selectable lying around like the above test case.
        # renaming this method to _setUp will ignore it and
        # this test case pass with flying colors
        f = protocol.Factory()
        f.protocol = protocol.Protocol()
        reactor.listenTCP(0, f, interface="127.0.0.1")

    def test_example2(self):
        d = defer.Deferred()
        d.addCallback(self._cb)
        reactor.callLater(1, d.callback, 'hi')

        failure = util.deferredError(d)
        assertEquals(failure.type, "this sucks")
        # if you see this, then it means that this test passed.
        print "\nRETURNING None FROM TEST METHOD"

    def _cb(self, result):
        raise "this sucks"

# dummy realm for testing
class MyRealm:
    implements(portal.IRealm)
    def requestAvatar(self, avatarId, mind, *interfaces):
        return (perspective.IPerspective, pb.Avatar(), lambda:None)
