from twisted.trial import unittest
from twisted.internet import defer
from twisted.python import log

from twisted.words.protocols.jabber import xmlstream
from twisted.words.test.test_jabberxmlstream import IQTest

class TimeoutTestCase(IQTest):
    
    def testTimeoutTypeResult(self):
        """
        Test that an iq with type result does not cause a timeout, 
        even if one is set.
        """
        self.iq.timeout = 60

        self.iq['type'] = 'result'

        d = self.iq.send()
        self.clock.pump([1, 60])
        self.failIf(self.clock.calls)
        self.failIf(hasattr(self.xmlstream, 'iqDeferreds'))
        return d
        
