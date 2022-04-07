from twisted.trial import unittest
from twisted.internet import defer

class InlineTestCase(unittest.TestCase):
    @defer.inlineCallbacks
    def iAmEmpty(self):
        pass

    def testEmpty(self):
        d = self.iAmEmpty()
	d.addCallbacks(lambda _: None, 
                       lambda _: self.fail('empty function raised exception'))
	return d
