from twisted.python import log
from twisted.internet import defer

def a(): 1/0

@defer.inlineCallbacks
def f(d):
    yield d

def informative_log():
    d=defer.Deferred()
    f(d).addErrback(log.err)
    try: a()
    # d.errback()'s calls the inlineCallback registration before
    # returning, so d.result.tb is informative and all is well in log.err
    except: d.errback()

def uninformative_log():
    d=defer.Deferred()
    try: a()
    except: d.errback()
    # d.errback() returns before any registrations are added on it, so
    # d.result.tb is now None before inlineCallback had a chance to
    # register on errbacks, and this log.err is not informative.
    f(d).addErrback(log.err)
