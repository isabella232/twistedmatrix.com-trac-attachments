#!/usr/bin/env python

import StringIO

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ClientCreator
from twisted.protocols import basic

#from twisted.protocols import htb
import htb2 as htb

class Echo(Protocol):
    def connectionMade(self):
        print 'connected!'
        self.fileTransfer = None
        
    def dataReceived(self, data):
        count = int(data)
        #self.transport.write('a'*(count))

        def _sendFile(ignore=None):
            print 'sending %r bytes' % (count,)
            print "self.transport.consumer.producer: %r" % self.transport.consumer.producer
            self.transport.write('sending you %d' % (count,))
            sender = basic.FileSender()
            self.fileTransfer = sender.beginFileTransfer(StringIO.StringIO('a'*(count)), self.transport)

        if self.fileTransfer is not None:
            print 'still transfering, queuing to send after this is done'
            self.fileTransfer.addCallback(_sendFile)
            return

        _sendFile()
        
        def _finish2(res):
            print 'done'
            print "self.transport.consumer.producer: %r" % self.transport.consumer.producer
            self.fileTransfer = None
        self.fileTransfer.addCallback(_finish2)

if True:
    filter = htb.HierarchicalBucketFilter()
    bucket = htb.Bucket()
    filter.buckets[None] = bucket

    bucket.maxburst = 1 * 1024
    bucket.rate = 1 * 1024
    
    protocol = htb.ShapedProtocolFactory(Echo, filter)
else:
    protocol = Echo

c = ClientCreator(reactor, protocol)
def gotProtocol(p):
    p.sendMessage(1024*1024*10)
    reactor.callLater(2, p.transport.loseConnection)
c.connectTCP("localhost", 8007) #.addCallback(gotProtocol)
reactor.run()
