#!/usr/bin/env python

from time import sleep
from queue import Queue
from twisted.internet import reactor
from twisted.internet.defer import Deferred, succeed, gatherResults
from twisted.internet.task import LoopingCall
from twisted.python import log

import logging
logging.basicConfig()

observer = log.PythonLoggingObserver(loggerName="testfile")
observer.start()


def t():
    q = Queue()

    def p():
        sleep(0.0001)
        return succeed(None)

    def f(*a, **kw):
        d = Deferred()
        q.put(d)
        return p().chainDeferred(d)

    for i in xrange(4):
        reactor.callInThread(f)

    return gatherResults([q.get() for _ in xrange(4)], consumeErrors=True)

if __name__ == "__main__":
    l = LoopingCall(reactor.callInThread, t)
    l.start(0.005, now=True)
    reactor.run()
