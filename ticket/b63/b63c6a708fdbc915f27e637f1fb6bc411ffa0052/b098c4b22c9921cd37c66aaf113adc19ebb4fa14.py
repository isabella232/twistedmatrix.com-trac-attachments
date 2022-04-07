from twisted.python import log
import sys
log.startLogging(sys.stdout)

from twisted.internet import protocol

class PP(protocol.ProcessProtocol):
    def __init__(self, fds):
        self.__fds = fds

    def outReceived(self, bytes):
        print self.__fds, 'out received', repr(bytes)
    
    def errReceived(self, bytes):
        print self.__fds, 'err received', repr(bytes)
    
    def processEnded(self, status):
        print 'process ended'
        if self.__fds is not None:
            print 'Closing', self.__fds
            # os.close(self.__fds[0])
            # os.close(self.__fds[1])
            self.transport.closeChildFD(self.__fds[0])
            self.transport.closeChildFD(self.__fds[1])
        else:
            # Time to leave
            reactor.stop()

import os

def start():
    fileObj = file('.bashrc')
    r1, w1 = os.pipe()
    r2, w2 = os.pipe()
    r3, w3 = os.pipe()
    
    p1 = PP((r1, w1))
    p2 = PP((r2, w2))
    p3 = PP((r3, w3))
    p4 = PP(None)
    reactor.spawnProcess(p1, '/bin/cat', ['cat1'], childFDs={0: fileObj.fileno(),
                                                             1: w1, 2: 'r'})
    reactor.spawnProcess(p2, '/bin/cat', ['cat2'], childFDs={0: r1,
                                                             1: w2, 2: 'r'})
    reactor.spawnProcess(p3, '/bin/cat', ['cat3'], childFDs={0: r2,
                                                             1: w3, 2: 'r'})
    reactor.spawnProcess(p4, '/bin/cat', ['cat4'], childFDs={0: r3,
                                                             1: 'r', 2: 'r'})

from twisted.internet import reactor
reactor.callWhenRunning(start)
reactor.run()
