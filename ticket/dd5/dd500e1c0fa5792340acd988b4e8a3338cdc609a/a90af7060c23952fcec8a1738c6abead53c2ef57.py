#!/usr/bin/python
import time
from twisted.internet import reactor
from twisted.python import threadable
threadable.init(1)
from twisted.internet import threads
from threading import Event

e = Event()
e.clear()
def aWaitingThread(i):
    print 'Running job', i
    e.wait()
    print 'Job', i, 'done'

def unblockEvent():
    print 'Unblocking'
    e.set()

def checkStatus():
    if e.isSet():
        reactor.stop()
        return
    print 'Failing to run scheduled jobs in threads'
    print len(reactor.threadpool.threads), 'threads in pool.'
    print len(reactor.threadpool.working), 'threads working.'
    print reactor.threadpool.q.qsize(), 'jobs in workqueue.'
    reactor.stop()

def startThreads2(x):
    # One thread is started. Give it time to add itself to waiters list
    time.sleep(1)
    
    for i in xrange(3):
        print 'Scheduling job', i
        reactor.callInThread(aWaitingThread, i)
    print 'Scheduling unblock!'
    reactor.callInThread(unblockEvent)
    reactor.callLater(3, checkStatus)

def runInThread():
    return

def startThreads():
    # Get one thread started
    d = threads.deferToThread(runInThread)
    d.addCallback(startThreads2)
    
reactor.callLater(0, startThreads)
reactor.run()
print 'Done'
