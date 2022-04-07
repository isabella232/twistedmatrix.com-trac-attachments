from twisted.trial import unittest

class Foo(unittest.TestCase):
    skip = 'yes'

    def setUpClass(self):
        print 'CLASS SET UP RAAAAAAAAR'
    
    def testBar(self):
        pass