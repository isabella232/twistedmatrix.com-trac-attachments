class NonThreadPool(object):
    """
    A stand-in for ``twisted.python.threadpool.ThreadPool`` so that the
    majority of the test suite does not need to use multithreading.

    This implementation takes the function call which is meant to run in a
    thread pool and runs it synchronously in the calling thread.

    :ivar int calls: The number of calls which have been dispatched to this
        object.
    """
    calls = 0

    def callInThreadWithCallback(self, onResult, func, *args, **kw):
        self.calls += 1
        try:
            result = func(*args, **kw)
        except:
            onResult(False, Failure())
        else:
            onResult(True, result)


class NonReactor(object):
    """
    A stand-in for ``twisted.internet.reactor`` which fits into the execution
    model defined by ``NonThreadPool``.
    """
    def callFromThread(self, f, *args, **kwargs):
        f(*args, **kwargs)


