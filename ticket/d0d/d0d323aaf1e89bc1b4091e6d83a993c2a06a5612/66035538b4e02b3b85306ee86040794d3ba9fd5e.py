
from twisted.protocols import amp
from twisted.trial import unittest

from twisted.test.test_amp import connectedServerAndClient

class SomeError(Exception):
    pass

class SomeCommand(amp.Command):
    errors = { SomeError: 'SOME_ERROR' }


class AnotherCommand(SomeCommand):
    pass


class SomeProtocol(amp.AMP):
    @AnotherCommand.responder
    def command2(self):
        raise SomeError()


class AmpTestCase(unittest.TestCase):

    def testErrorPropagation(self):
        """
        Verify that errors specified in a superclass command are propagated to
        its subclasses.
        """
        c, s, p = connectedServerAndClient(ServerClass=SomeProtocol,
                                           ClientClass=SomeProtocol)
        d = c.callRemote(AnotherCommand)
        d2 = self.failUnlessFailure(d, SomeError)
        p.flush()
        return d2


