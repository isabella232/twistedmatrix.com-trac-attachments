#!/usr/bin/env python2.5
from twisted.internet import defer, reactor
from twisted.python import failure
from twisted.python.util import mergeFunctionMetadata

import time, gc

## defgen

# BaseException is only in Py 2.5.
try:
    BaseException
except NameError:
    BaseException=Exception


# inlineCallbacks with slightly buggy speed hack:
def _faster_inlineCallbacks(result, g, deferred):
    # improvement: shortcirtuit already trigered deferreds
    while 1:
        try:
            # Send the last result back as the result of the yield expression.
            if isinstance(result, failure.Failure):
                result = g.throw(result.type, result.value, result.tb)
            else:
                result = g.send(result)
        except StopIteration:
            # fell off the end, or "return" statement
            deferred.callback(None)
            return deferred
        except defer._DefGen_Return, e:
            # returnVal call
            deferred.callback(e.value)
            return deferred
        except:       
            deferred.errback()
            return deferred

        if isinstance(result, defer.Deferred):
            # a deferred was yielded, get the result.
            if result.called:
                # XXX this test is buggy
                result = result.result
                continue

            def gotResult(r):
                _faster_inlineCallbacks(r, g, deferred)

            result.addBoth(gotResult)
            return deferred

    return deferred


def faster_inlineCallbacks(f):
    def unwindGenerator(*args, **kwargs):
        return _faster_inlineCallbacks(None, f(*args, **kwargs), defer.Deferred())
    return mergeFunctionMetadata(f, unwindGenerator)


#### Itamar's version - untested error handling path

class _Result(object):
    def __init__(self):
        self._def = defer.Deferred()
        self.returnVal = self._def.callback
        
    def wait(self, d):
        d.pause()
        d.addCallbacks(self._result, self._error)
        return d
    
    def _error(self, flr):
        try:
            d = self._gen.throw(flr.type, flr.value, flr.tb)
            if d is not None: 
                d.unpause()
        except:
            self._gen.errback(failure.Failure())
            
    def _result(self, result):
        try:
            d = self._gen.send(result)
            if d is not None:
                d.unpause()
        except:
            self._gen.errback(failure.Failure())

def itamar_inlineCallbacks(f):
    def wrapper(*args, **kwargs):
        r = _Result()
        r._gen = f(r, *args, **kwargs)
        try:
            d = r._gen.next()
            if d is not None:
                d.unpause()
        except:
            r._def.errback(failure.Failure())
        return r._def
    return mergeFunctionMetadata(f, wrapper)


### Benchmarkable functions for different variations:

# twisted 2.1 deferredGenerator
@defer.deferredGenerator
def defgen21(iters, df):
    for i in range(iters):
        d = df(i)
        d = defer.waitForDeferred(d)
        yield d
        n = d.getResult()
    yield n + 1

# itamar's inlineCallbacks
@itamar_inlineCallbacks
def itamar(result, iters, df):
    for i in range(iters):
        n = yield result.wait(df(i))
    yield result.returnVal(n + 1)

# twisted 2.5 inlineCallbacks
@defer.inlineCallbacks
def inlineCallbacks25(iters, df):
    for i in range(iters):
        n = yield df(i)
    defer.returnValue(n + 1)

# twisted 2.5 inlineCallbacks with speed optimization
@faster_inlineCallbacks
def faster_inlineCallbacks25(iters, df):
    for i in range(iters):
        n = yield df(i)
    defer.returnValue(n + 1)


def imDone(res, func, then):
    elapsed = time.clock() - then
    print "%0.3f secs  <--  %s (result=%s)" % (elapsed, func.func_name, res[0])

def err(flr):
    print "failure: %s" % flr


def pretriggeredDeferred(i):
    """Deferred that is already triggered."""
    return defer.succeed(i)

def callLaterDeferred(i):
    """Deferred that isn't immediately triggered (benchmarks slower due to callLater)."""
    d = defer.Deferred()
    reactor.callLater(0, d.callback, i)
    return d
    
def go(numDeferreds, benchmarkedFunction, deferredFactory):
    """Run benchmarked function 10000 times with numDeferreds created.

    Uses deferredFactory to create Deferreds.
    """
    ir = range(1000)
    then = time.clock()
    defs = []
    for i in ir:
        defs.append(benchmarkedFunction(numDeferreds, deferredFactory))
    result = defer.gatherResults(defs)
    result.addCallback(imDone, benchmarkedFunction, then)
    result.addErrback(err)
    result.addCallback(lambda x: gc.collect())
    return result

def printer(_x, m):
    print m


def runall(df):
    print "\n==== %s" % (df.__doc__.strip(),)
    result = defer.succeed(1)
    for i in (3, 10, 50):
        result.addCallback(printer, "== %d Deferreds" % (i,))
        for f in (defgen21, itamar,
                  inlineCallbacks25, faster_inlineCallbacks25):
            result.addCallback(lambda x, f=f: go(i, f, df))
    return result

def main():
    runall(pretriggeredDeferred).addCallback(
        lambda x: runall(callLaterDeferred)).addCallback(
        lambda x: reactor.stop())

reactor.callWhenRunning(main)
reactor.run()
