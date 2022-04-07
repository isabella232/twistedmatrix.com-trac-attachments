from twisted.internet import defer
from twisted.trial import unittest
class InlineDefTest(unittest.TestCase):
    def testDoubleIndirect(self):
        return F0().addCallbacks(ok, nok)
    def testIndirect(self):
        return F1().addCallbacks(ok, nok)
    def testDirect(self):
        return F2().addCallbacks(ok, nok)
    def testCall(self):
        return F3().addCallbacks(ok, nok)
    def testFinallyGenerator(self):
        return FT().addCallbacks(ok, nok)
def ok(r):  assert 0
def nok(r):
    tb = r.getTraceback()
    assert 'in F3' in tb, tb
@defer.inlineCallbacks
def F3():
    1 / 0
    d = defer.Deferred()
    d.callback(1)
    yield d
@defer.inlineCallbacks
def F2():
    try:
        d = defer.Deferred()
        d.callback(1)
        yield d
        yield F3()
    finally:
        pass
@defer.inlineCallbacks
def F1():
    yield F2()
def F0():
    return F1().addErrback(lambda x:x)
@defer.inlineCallbacks
def FT():
    try:
        yield F3()
    finally:
        d = defer.Deferred()
        d.callback(1)
        yield d
