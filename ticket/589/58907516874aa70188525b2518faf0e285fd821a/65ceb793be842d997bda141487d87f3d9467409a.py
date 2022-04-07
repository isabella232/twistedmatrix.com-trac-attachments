
from twisted.trial import unittest
from twisted.python import log, failure

class One(unittest.TestCase):
    def test1(self):
        pass

    def test2(self):
        f1 = failure.Failure(RuntimeError("oops"))
        log.err(f1)
        raise KeyError("uh oh")

    def test3(self):
        pass

