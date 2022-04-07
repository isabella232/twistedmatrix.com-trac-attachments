#!/usr/bin/env python
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.
from __future__ import print_function

import gc
gc.enable()

from twisted.internet import reactor, task
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory,ReconnectingClientFactory
from twisted.protocols.basic import LineReceiver



class EchoClient(LineReceiver):
    end = "Bye-bye!"

    def connectionMade(self):
        self.sendLine("Hello, world!")
        self.sendLine("What a fine day it is.")
        self.sendLine(self.end)


    def lineReceived(self, line):        
        if line == self.end:
            self.transport.loseConnection()

REFERRERS_TO_IGNORE = [ locals(), globals(), gc.garbage ]

class EchoClientFactory(ClientFactory):

    def buildProtocol(self,addr):
        self.protocol = EchoClient()        
        gc.collect()        
        referrers = [r for r in gc.get_referrers(self) if r not in REFERRERS_TO_IGNORE]
        print('Total References:',len(referrers))
        for ref in referrers:                        
            if type(ref) is dict:
                print(ref)        
        return self.protocol

    def clientConnectionFailed(self, connector, reason):
        self.protocol = None
        reactor.callLater(0,connector.connect) ## LEAKS
        #connector.connect() ## DOES NOT LEAK

    def clientConnectionLost(self, connector, reason):
        self.protocol = None
        reactor.callLater(0,connector.connect)  ## LEAKS
        #connector.connect() ## DOES NOT LEAK


factory = EchoClientFactory()
reactor.connectTCP('localhost', 8000, factory)
reactor.run()

