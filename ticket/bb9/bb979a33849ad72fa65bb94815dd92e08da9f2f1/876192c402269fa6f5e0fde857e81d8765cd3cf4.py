from twisted.test.proto_helpers import StringTransport
from twisted.trial import unittest

from twisted.protocols import amp
from twisted.internet import protocol, reactor

import struct

class MockCommand(amp.Command):
    arguments = [('optArg',amp.String(optional = True))]
    response = [('result',amp.Boolean())]

class TestProtocol(amp.AMP):
    def mockResponder(self,optArg=None):
        return {'result':(optArg is not None)}
    MockCommand.responder(mockResponder)

    def doSomethingWrong(self):
        d = self.callRemote(MockCommand,thisargdoesntexist="hello")
        return d.addCallback(lambda res: res['result'])


class callRemoteWrongSignature(unittest.TestCase):
    def setUp(self):
        self.proto = TestProtocol()
        t = StringTransport()
        t.protocol = self.proto
        self.proto.makeConnection(t)

    def test_WrongParam(self):
        self.assertRaises(amp.InvalidSignature,self.proto.doSomethingWrong)

