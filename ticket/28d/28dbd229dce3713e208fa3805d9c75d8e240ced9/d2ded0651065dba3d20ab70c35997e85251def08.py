#!/usr/bin/python

from twisted.internet import reactor
from threading import Thread, currentThread
from time import sleep

class OtherThread(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        count = 0
        while 1:
            print "OtherThread: Running %d" % count
            if count == 8:
                print "OtherThread: Scheduling bar"
                #reactor.callLater(0, printResult, 'bar')
                reactor.callFromThread(printResult, 'bar')
            count = count + 1
            sleep(0.1)

otherThread = OtherThread()
otherThread.setDaemon(True)
otherThread.start()

def printResult(result):
    print "RESULT: %s %s" % (currentThread(), result)

def test():
    print "<TEST>"
    reactor.callLater(0.2, printResult, 'foo')
    print "</TEST>"

reactor.callLater(0.4, test)
reactor.callLater(2.4, test)
reactor.callLater(4.0, reactor.stop)
reactor.run()


