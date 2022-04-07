from twisted.internet.defer import timeout, Deferred

class SlotsDeferred(object):
    __slots__ = ['debug', 'callbacks', 'called', 'paused', 'result', 'timeoutCall', '_runningCallbacks', '_debugInfo']

    # Normal Deferred follow
    called = 0
    paused = 0
    timeoutCall = None
    _debugInfo = None

    # Are we currently running a user-installed callback?  Meant to prevent
    # recursive running of callbacks when a reentrant call to add a callback is
    # used.
    _runningCallbacks = False

    # Keep this class attribute for now, for compatibility with code that
    # sets it directly.
    debug = False

    def __init__(self):
        self.callbacks = []
        if self.debug:
            self._debugInfo = DebugInfo()
            self._debugInfo.creator = traceback.format_stack()[:-1]

    def addCallbacks(self, callback, errback=None,
                     callbackArgs=None, callbackKeywords=None,
                     errbackArgs=None, errbackKeywords=None):
        """Add a pair of callbacks (success and error) to this Deferred.

        These will be executed when the 'master' callback is run.
        """
        assert callable(callback)
        assert errback == None or callable(errback)
        cbs = ((callback, callbackArgs, callbackKeywords),
               (errback or (passthru), errbackArgs, errbackKeywords))
        self.callbacks.append(cbs)

        if self.called:
            self._runCallbacks()
        return self

    def addCallback(self, callback, *args, **kw):
        """Convenience method for adding just a callback.

        See L{addCallbacks}.
        """
        return self.addCallbacks(callback, callbackArgs=args,
                                 callbackKeywords=kw)

    def addErrback(self, errback, *args, **kw):
        """Convenience method for adding just an errback.

        See L{addCallbacks}.
        """
        return self.addCallbacks(passthru, errback,
                                 errbackArgs=args,
                                 errbackKeywords=kw)

    def addBoth(self, callback, *args, **kw):
        """Convenience method for adding a single callable as both a callback
        and an errback.

        See L{addCallbacks}.
        """
        return self.addCallbacks(callback, callback,
                                 callbackArgs=args, errbackArgs=args,
                                 callbackKeywords=kw, errbackKeywords=kw)

    def chainDeferred(self, d):
        """Chain another Deferred to this Deferred.

        This method adds callbacks to this Deferred to call d's callback or
        errback, as appropriate. It is merely a shorthand way of performing
        the following::

            self.addCallbacks(d.callback, d.errback)

        When you chain a deferred d2 to another deferred d1 with
        d1.chainDeferred(d2), you are making d2 participate in the callback
        chain of d1. Thus any event that fires d1 will also fire d2.
        However, the converse is B{not} true; if d2 is fired d1 will not be
        affected.
        """
        return self.addCallbacks(d.callback, d.errback)

    def callback(self, result):
        """Run all success callbacks that have been added to this Deferred.

        Each callback will have its result passed as the first
        argument to the next; this way, the callbacks act as a
        'processing chain'. Also, if the success-callback returns a Failure
        or raises an Exception, processing will continue on the *error*-
        callback chain.
        """
        assert not isinstance(result, Deferred)
        self._startRunCallbacks(result)


    def errback(self, fail=None):
        """Run all error callbacks that have been added to this Deferred.

        Each callback will have its result passed as the first
        argument to the next; this way, the callbacks act as a
        'processing chain'. Also, if the error-callback returns a non-Failure
        or doesn't raise an Exception, processing will continue on the
        *success*-callback chain.

        If the argument that's passed to me is not a failure.Failure instance,
        it will be embedded in one. If no argument is passed, a failure.Failure
        instance will be created based on the current traceback stack.

        Passing a string as `fail' is deprecated, and will be punished with
        a warning message.
        """
        if not isinstance(fail, failure.Failure):
            fail = failure.Failure(fail)

        self._startRunCallbacks(fail)


    def pause(self):
        """Stop processing on a Deferred until L{unpause}() is called.
        """
        self.paused = self.paused + 1


    def unpause(self):
        """Process all callbacks made since L{pause}() was called.
        """
        self.paused = self.paused - 1
        if self.paused:
            return
        if self.called:
            self._runCallbacks()

    def _continue(self, result):
        self.result = result
        self.unpause()

    def _startRunCallbacks(self, result):
        if self.called:
            if self.debug:
                if self._debugInfo is None:
                    self._debugInfo = DebugInfo()
                extra = "\n" + self._debugInfo._getDebugTracebacks()
                raise AlreadyCalledError(extra)
            raise AlreadyCalledError
        if self.debug:
            if self._debugInfo is None:
                self._debugInfo = DebugInfo()
            self._debugInfo.invoker = traceback.format_stack()[:-2]
        self.called = True
        self.result = result
        if self.timeoutCall:
            try:
                self.timeoutCall.cancel()
            except:
                pass

            del self.timeoutCall
        self._runCallbacks()

    def _runCallbacks(self):
        if self._runningCallbacks:
            # Don't recursively run callbacks
            return
        if not self.paused:
            while self.callbacks:
                item = self.callbacks.pop(0)
                callback, args, kw = item[
                    isinstance(self.result, failure.Failure)]
                args = args or ()
                kw = kw or {}
                try:
                    self._runningCallbacks = True
                    try:
                        self.result = callback(self.result, *args, **kw)
                    finally:
                        self._runningCallbacks = False
                    if isinstance(self.result, Deferred):
                        # note: this will cause _runCallbacks to be called
                        # recursively if self.result already has a result.
                        # This shouldn't cause any problems, since there is no
                        # relevant state in this stack frame at this point.
                        # The recursive call will continue to process
                        # self.callbacks until it is empty, then return here,
                        # where there is no more work to be done, so this call
                        # will return as well.
                        self.pause()
                        self.result.addBoth(self._continue)
                        break
                except:
                    self.result = failure.Failure()

        if isinstance(self.result, failure.Failure):
            self.result.cleanFailure()
            if self._debugInfo is None:
                self._debugInfo = DebugInfo()
            self._debugInfo.failResult = self.result
        else:
            if self._debugInfo is not None:
                self._debugInfo.failResult = None

    def setTimeout(self, seconds, timeoutFunc=timeout, *args, **kw):
        """Set a timeout function to be triggered if I am not called.

        @param seconds: How long to wait (from now) before firing the
        timeoutFunc.

        @param timeoutFunc: will receive the Deferred and *args, **kw as its
        arguments.  The default timeoutFunc will call the errback with a
        L{TimeoutError}.
        """
        warnings.warn(
            "Deferred.setTimeout is deprecated.  Look for timeout "
            "support specific to the API you are using instead.",
            DeprecationWarning, stacklevel=2)

        if self.called:
            return
        assert not self.timeoutCall, "Don't call setTimeout twice on the same Deferred."

        from twisted.internet import reactor
        self.timeoutCall = reactor.callLater(
            seconds,
            lambda: self.called or timeoutFunc(self, *args, **kw))
        return self.timeoutCall

    def __str__(self):
        cname = self.__class__.__name__
        if hasattr(self, 'result'):
            return "<%s at %s  current result: %r>" % (cname, hex(unsignedID(self)),
                                                       self.result)
        return "<%s at %s>" % (cname, hex(unsignedID(self)))
    __repr__ = __str__

if __name__ == "__main__":
    #Cls = Deferred
    Cls = SlotsDeferred
    count = 250000
    print "Testing %s, creating %d instances on each step" % (Cls.__name__, count)
    import os
    pid = os.getpid()
    cmd = "ps -F %d" % pid
    a = [Cls() for _ in xrange(count)]
    os.system(cmd)
    b = [Cls() for _ in xrange(count)]
    os.system(cmd)
    c = [Cls() for _ in xrange(count)]
    os.system(cmd)
