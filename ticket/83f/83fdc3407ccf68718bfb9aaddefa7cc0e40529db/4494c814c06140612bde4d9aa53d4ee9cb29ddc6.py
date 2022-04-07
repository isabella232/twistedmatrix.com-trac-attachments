#
#  This interface is heavily inspired by twisted.internet.defer.
#  It's a little less extensible, but it won't let you blow the stack!
#

from microfailure import Failure

__all__ = ['AlreadyCalledError', 'succeed', 'passthrough', 'Deferred']

class AlreadyCalledError(Exception):
    pass

class _nothing(object):
    pass

def passthrough(arg):
    return arg

class Deferred(object):
    called = False
    inprocess = False
    waiting = []
    paused = 0
    count = 0
    
    def __init__(self):
        Deferred.count += 1
        self.count = Deferred.count
        self.callbacks = []
        self.waiting = False
            
    def addCallbacks(self, callback=passthrough, errback=passthrough,
        callbackArgs=(), callbackKeywords={},
        errbackArgs=(), errbackKeywords={}):
        self.callbacks.append(((callback, callbackArgs, callbackKeywords),
            (errback, errbackArgs, errbackKeywords)))
        if self.called:
            self._runCallbacks()
        return self

    def addCallback(self, callback, *args, **kwargs):
        return self.addCallbacks(
            callback=callback, callbackArgs=args, callbackKeywords=kwargs)

    def addErrback(self, errback, *args, **kwargs):
        return self.addCallbacks(
            errback=errback, errbackArgs=args, errbackKeywords=kwargs)

    def addBoth(self, both, *args, **kwargs):
        return self.addCallbacks(
            callback=both, errback=both, callbackArgs=args,
            callbackKeywords=kwargs, errbackArgs=args, errbackKeywords=kwargs)

    def fork(self):
        return succeed(self)

    def pause(self):
        self.paused += 1

    def unpause(self):
        self.paused -= 1
        if not self.paused and self.called:
            self._runCallbacks()

    def _continue(self, result):
        self.result = result
        self.unpause()

    def callback(self, result):
        self._startRunCallbacks(result)
        return self

    def errback(self, fail=None):
        if not isinstance(fail, Failure):
            fail = Failure(fail)
        self._startRunCallbacks(fail)
        return self

    def _startRunCallbacks(self, result):
        if self.called:
            raise AlreadyCalledError
        self.called = True
        self.result = result
        self._runCallbacks()

    def _runCallbacks(self):
        # wow is this scary :)
        waiting = Deferred.waiting
        if not self.waiting:
            waiting.append(self)
        if Deferred.inprocess:
            return
        Deferred.inprocess = True
        while waiting:
            self = waiting.pop()
            self.waiting = False
            # implicit callback chaining
            if isinstance(self.result, Deferred):
                self.pause()
                self.result.addBoth(self._continue)
            elif not self.paused:
                cb = self.callbacks
                while cb:
                    fn, args, kwargs = cb.pop(0)[isinstance(self.result, Failure)]
                    try:
                        self.result = fn(self.result, *args, **kwargs)
                        if isinstance(self.result, Deferred):
                            self.pause()
                            self.result.addBoth(self._continue)
                            break
                    except:
                        self.result = Failure()
            if isinstance(self.result, Failure):
                self.result.cleanFailure()
        Deferred.inprocess = False

    def __str__(self):
        if hasattr(self, 'result'):
            res = self.result
            if isinstance(res, Deferred):
                return "<Deferred #%s current: [Deferred #%s]>" % (
                    self.count, res.count)
            return "<Deferred #%s current: %r>" % (
                self.count, res)
        return "<Deferred #%s>" % (self.count,)
    __repr__ = __str__
        
class succeed(Deferred):
    called = True
    def __init__(self, result):
        Deferred.__init__(self)
        self.result = result
    
class fail(Deferred):
    called = True
    def __init__(self, result=_nothing):
        Deferred.__init__(self)
        self.result = result is _nothing and Failure() or result
 
if __name__ == '__main__':
    end = 10000
    values = iter(range(end+1))
    def print_(v):
        print v
    def next(v):
        if v < end:
            return succeed(values.next()).addCallback(next)
        return v
    rv = succeed(values.next()).addCallback(next).addCallback(print_)
