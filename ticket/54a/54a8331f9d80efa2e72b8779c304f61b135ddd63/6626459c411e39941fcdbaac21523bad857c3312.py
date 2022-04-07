from twisted.trial.unittest import SynchronousTestCase

from twisted.internet.defer import fail

class MyTest(SynchronousTestCase):

    def test_1(self):
        fail(Exception("Oops"))
        self.assertTrue(False)

    def test_2(self):
        self.assertFalse(False)
