#!/usr/bin/env python

from twisted.internet.protocol import Protocol, Factory
from twisted.protocols import policies, basic
from twisted.internet import reactor

import htb_alt


class Echo(Protocol):
    magic = 1024*10
    def connectionMade(self):
        self.sendRequest()

    def sendRequest(self):
        print 'sendRequest'
        self.transport.write(str(self.magic))
        self.byteCount = 0
    
    def dataReceived(self, data):
        self.byteCount += len(data)
        print 'got %d of %d' % (self.byteCount, self.magic,)
        if self.byteCount >= self.magic:
            self.sendRequest()
factory = Factory()
factory.protocol = Echo

reactor.listenTCP(8007, factory)
print 'run'
reactor.run()
