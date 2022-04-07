
from twisted.trial import unittest, util
from twisted.python import log
from twisted.internet import defer

class FakeException(Exception):
    pass

def die():
    try:
        raise FakeException()
    except:
        log.err()

class MyTest(unittest.TestCase):
    def testFlushAfterWait(self):
        die()
        util.wait(defer.succeed(''))
        log.flushErrors(FakeException)

    def testFlushByItself(self):
        die()
        log.flushErrors(FakeException)
