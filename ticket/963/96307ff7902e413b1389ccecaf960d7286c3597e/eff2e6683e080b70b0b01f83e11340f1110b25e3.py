
from twisted.trial import unittest

class TestCase(unittest.TestCase):

    def testAssertIsInstance(self):
        self.assertIsInstance(dict(), dict)
        self.assertIsInstance(dict(), dict, '')

    def testAssertDictEqual(self):
        self.assertDictEqual(dict(), dict())


if __name__ == '__main__':
    unittest.main()

