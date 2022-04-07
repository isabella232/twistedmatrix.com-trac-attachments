import os

from zope.interface import implements

from twisted.trial import unittest
from twisted.internet import interfaces, reactor, defer


class TestRemovingDescriptor(object):

    implements(interfaces.IReadDescriptor)

    def __init__(self, reactor):
        self.reactor = reactor

        self.read, self.write = os.pipe()
        self.d = defer.Deferred()
        self.insideReactor = False

    def start(self):
        self.reactor.addReader(self)
        self.insideReactor = True
        os.write(self.write, 'a')
        return self.d

    def doRead(self):
        self.reactor.removeReader(self)
        self.insideReactor = False
        self.d.callback(self)

    def logPrefix(self):
        return 'foo'

    def fileno(self):
        assert self.insideReactor, "fileno() called outside of the reactor"
        return self.read

    def connectionLost(self, reason):
        pass



class FileDescriptorTestCase(unittest.TestCase):

    def test_removeFromReactor(self):
        return TestRemovingDescriptor(reactor).start()
