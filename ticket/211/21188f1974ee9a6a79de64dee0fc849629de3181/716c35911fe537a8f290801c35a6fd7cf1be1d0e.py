#!/usr/bin/env python
from twisted.trial import unittest
from twisted.protocols import sip
from twisted.internet import defer, reactor

BSP_IP = "172.16.1.33"
BSP_PORT = "5060"

class Client(sip.Base):
    def __init__(self):
        sip.Base.__init__(self)
        self.received = []
    def handle_response(self,response,addr):
        self.received.append(response)

class sipTest(unittest.TestCase):

    def setUp(self):
        self.proxy = sip.RegisterProxy(host=BSP_IP)
        self.registry = sip.InMemoryRegistry("bell.example.com")
        self.proxy.registry = self.proxy.locator = self.registry
        self.serverPort = reactor.listenUDP(0, self.proxy, interface=BSP_IP)
        self.client = Client()
        self.clientPort = reactor.listenUDP(0, self.client, interface=BSP_IP)
        self.serverAddress = self.serverPort.getHost().host

    def tearDown(self):
        self.clientPort.stopListening()
        self.serverPort.stopListening()
        for d, uri in self.registry.users.values():
            d.cancel()
        #reactor.iterate()
        #reactor.iterate()

    def testRegister():
        print self.clientPort.getHost()
        p = self.clientPort.getHost()[-1]
        r = sip.Request("REGISTER", "sip:bell.example.com")
        r.addHeader("to", "sip:joe@bell.example.com")
        r.addHeader("contact", "sip:joe@127.0.0.1:%d" % p)
        r.addHeader("via", sip.Via(BSP_IP, port=p).toString())
        self.client.sendMessage(sip.URL(host=BSP_IP, port=self.serverAddress[1]),
                                r)
        while not len(self.client.received):
            reactor.iterate()
        self.assertEquals(len(self.client.received), 1)
        r = self.client.received[0]
        print r
        self.assertEquals(r.code, 200)
