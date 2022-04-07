#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf8

from twisted.internet import reactor
from twisted.internet.defer import fail
from twisted.python.failure import Failure

def gen():
    while True:
        yield 1

def gen2():
    yield 1
    raise ValueError, "some error"

def handleError(f, g):
    f.throwExceptionIntoGenerator(g)


def start():
    g1 = gen()
    g1.next()
    g2 = gen2()
    g2.next()
    try:
        g2.send(None)
    except:
        d = fail(Failure())
        d.addErrback(handleError, g2)

if __name__ == "__main__":
    reactor.callWhenRunning(start)
    reactor.run()
