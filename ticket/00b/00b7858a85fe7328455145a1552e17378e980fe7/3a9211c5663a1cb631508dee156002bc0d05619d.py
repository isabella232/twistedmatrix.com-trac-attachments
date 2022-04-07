from twisted.internet.protocol import Protocol, Factory

import os
import sys
if os.name == 'nt':
    try:
        from twisted.internet import iocpreactor
        iocpreactor.proactor.install()
    except:
        pass
else:
    try:
        from twisted.internet import pollreactor
        pollreactor.install()
    except:
        pass

#the default reactor is select-based, and will be install()ed if another has not    
from twisted.internet import reactor, task

class QOTD(Protocol):

    def connectionMade(self):
        print "connectionMade"
        self.last = 9
        t = task.LoopingCall(self.transport.resumeProducing)
        t.start(0.5)

    def connectionLost(self, reason):
        print "connectionLost"

    def dataReceived(self, data):
        for d in data:
            next = self.last + 1
            next = next % 10
            if next != int(d):
                print "ERROR: got %s instead of %s" % (int(d), next)
            self.last = int(d)


# Next lines are magic:
factory = Factory()
factory.protocol = QOTD

# 8007 is the port you want to run under. Choose something >1024
reactor.listenTCP(8007, factory)
reactor.run()
