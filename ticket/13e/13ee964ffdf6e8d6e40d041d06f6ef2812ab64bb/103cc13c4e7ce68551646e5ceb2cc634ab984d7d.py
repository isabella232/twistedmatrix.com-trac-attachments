from twisted.trial import unittest
class TestSetUpClass(unittest.TestCase):
    setUpCalled=0
    setUp2Called=0
    def setUpClass(self):
        print "setUpClass!"
        self.setUpCalled=1

    def test_foo(self):
        self.assert_(self.setUpCalled)
        self.assertFalse(self.setUp2Called)
        pass

class TestSetUpClass2(TestSetUpClass):
    def setUpClass(self):
        print "setUpClass2!"
        self.setUp2Called=1

    def test_foo(self):
        self.assertFalse(self.setUpCalled)
        self.assertTrue(self.setUp2Called)

class TestInheritedSetUpClass(unittest.TestCase):
    setUpCalled=0
    setUp2Called=0
    def setUpClass(self):
        print "TestInheritedSetUpClass.setUpClass!"
        if self.__class__ == TestInheritedSetUpClass:
            self.setUpCalled=1
        else:
            self.setUp2Called=1
    
    def test_foo(self):
        self.assert_(self.setUpCalled)
        self.assertFalse(self.setUp2Called)
        pass

class TestInheritedSetUpClass2(TestInheritedSetUpClass):
    def test_foo(self):
        self.assertFalse(self.setUpCalled)
        self.assertTrue(self.setUp2Called)

