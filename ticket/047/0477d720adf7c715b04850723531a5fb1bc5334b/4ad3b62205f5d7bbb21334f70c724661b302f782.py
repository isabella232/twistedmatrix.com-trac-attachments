from twisted.internet import defer
from twisted.trial import unittest

class TimeoutTest(unittest.TestCase):
    def testTimeoutErrorPropagation(self):
        def timedOut(err):
            print 'should get here with TimeoutError'
            print err

        d = defer.Deferred()
        d.addErrback(timedOut)
        return d
    testTimeoutErrorPropagation.timeout = 0.1
