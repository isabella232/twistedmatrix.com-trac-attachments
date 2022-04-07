import gc
import re
import sys
import weakref

from twisted.trial import unittest
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientCreator, ClientFactory
from twisted.protocols.basic import LineOnlyReceiver

class DummyProtocol(LineOnlyReceiver):
    def lineReceived(self, line):
        pass

class DummyFactory(ClientFactory):
    protocol = DummyProtocol

    def __init__(self):
        self.deferred = Deferred()
        self.reference = None

    def startedConnecting(self, connector):
        self.reference = weakref.ref(connector.transport)

    def clientConnectionFailed(self, connector, reason):
        reactor.callLater(0, self.deferred.callback, self.reference)

class BaseClientCircularReferenceTestCase(unittest.TestCase):
    _sys_version_re = re.compile(
                r'([\w.+]+)\s*'
                '\(#?([^,]+),\s*([\w ]+),\s*([\w :]+)\)\s*'
                '\[([^\]]+)\]?')

    def test_circularReferences(self):
        if not self._running_on_CPython():
            return
        was_enabled = gc.isenabled()
        gc.disable()

        factory = DummyFactory()
        reactor.connectTCP('255.255.255.255', 2, factory)
        d = factory.deferred
        d.addCallback(self._check_memory, was_enabled)
        return d

    def _check_memory(self, reference, enable_gc):
        self.failIf(reference() is not None, "Reference to Client still alive")
        
        if enable_gc:
            gc.enable()
    
    def _running_on_CPython(self):
        if sys.version[:10] == 'IronPython' or sys.platform[:4] == 'java':
            return False
        return self._sys_version_re.match(sys.version) is not None

