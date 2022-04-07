from zope.interface import implements

from twisted.internet.interfaces import IUDPTransport
from twisted.trial import unittest

from ..client import client

class FakeUdpTransport(object):
    """ Instead of connecting through the network, this transport 
    writes the broadcast messages to a variable that can be 
    checked. """

    implements(IUDPTransport)

    def __init__(self):
        self.msgs = []

    def write(self, packet, addr=None):
        self.msgs.append(repr(packet))

    def connect(host, port):
        pass

    def getHost():
        pass

    def stopListening():
        pass

class BroadcastServerTests(unittest.TestCase):
    def setUp(self):
        self.protocol = client.MulticastPingClient()
        self.tr = FakeUdpTransport()
        self.protocol.transport = self.tr
        
    def test_broadcast(self):
        self.protocol.startProtocol()
        self.assertTrue(len(self.tr.msgs) > 0)
        self.assertTrue(self.tr.msgs[0] == "'Client: Ping")