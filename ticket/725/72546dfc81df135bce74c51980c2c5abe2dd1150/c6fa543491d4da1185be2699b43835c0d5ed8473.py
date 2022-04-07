from twisted.internet import defer, threads, task, reactor
from twisted.trial import unittest

class SpecialException(Exception):
    pass

def failingThing():
    raise SpecialException("Failing thing is failing")

class Processor(object):
    @defer.inlineCallbacks
    def process(self):
        try:
            val = yield threads.deferToThread(failingThing)
        except SpecialException, e:
            self.rollback()

    def rollback(self):
        raise




class TestProcessor(unittest.TestCase):
    def testProcessor(self):
        p = Processor()
        return p.process()