import unittest
from twisted.internet.endpoints import _WrappingProtocol
from twisted.internet.endpoints import _WrappingFactory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.endpoints import SSL4ServerEndpoint
from twisted.internet.endpoints import SSL4ClientEndpoint
from twisted.internet.endpoints import UNIXServerEndpoint
from twisted.internet.endpoints import AdoptedStreamServerEndpoint




class _WrappingProtocolTestCase(unittest.TestCase):
    def test_WrappingProtocolTestCase(self):
        expected=_WrappingProtocol("test1","test2")
        actual=("_WrappingProtocol(test1,test2)")
        self.assertEqual(expected.__repr__(),actual)



class _WrappingFactoryTestCase(unittest.TestCase):
    def test_WrappingFactory(self):
        expected=_WrappingFactory('testString')
        actual=("_WrappingFactory(testString)")
        self.assertEqual(expected.__repr__(),actual)



class TCP4ServerEndpointTestCase(unittest.TestCase):
    def testTCP4ServerEndpoint(self):
        expected=TCP4ServerEndpoint(None,1234,56,'testString')
        actual=("TCP4ServerEndpoint(None,1234,backlog=56,interface=testString)")
        self.assertEqual(expected.__repr__(),actual)



class TCP4ClientEndpointTestCase(unittest.TestCase):
    def testTCP4ClientEndpoint(self):
        expected=TCP4ClientEndpoint(None,'test!',12345,676,(1,2,3))
        actual=("TCP4ClientEndpoint(None,test!,12345,timeout=676,bindAddress=(1, 2, 3))")
        print actual,expected
        self.assertEqual(expected.__repr__(),actual)



class SSL4ServerEndpointTestCase(unittest.TestCase):
    def testSSL4ServerEndpoint(self):
        expected=SSL4ServerEndpoint(None,12345,'test1',123,'test2')
        actual=("SSL4ServerEndpoint(None,12345,test1,backlog=123,interface=test2)")
        self.assertEqual(expected.__repr__(),actual)



class SSL4ClientEndpointTestCase(unittest.TestCase):
    def testSSL4ClientEndpoint(self):
        expected=SSL4ClientEndpoint(None,'host',1235,'test1',56,(1,'add'))
        actual=("SSL4ClientEndpoint(None,host,1235,test1,timeout=56,bindAddress=(1, 'add'))")
        self.assertEqual(expected.__repr__(),actual)



class UNIXServerEndpointTestCase(unittest.TestCase):
    def testUNIXServerEndpoint(self):
        expected=UNIXServerEndpoint(None,'add',456,0777,1)
        actual=("UNIXServerEndpoint(None,add,backlog=456,mode=511,wantPID=1)")

        self.assertEqual(expected.__repr__(),actual)

class AdoptedStreamServerEndpointTestCase(unittest.TestCase):
    def test_AdoptedStreamServerEndpoint(self):
        expected=AdoptedStreamServerEndpoint(None,1234,'address')
        actual=("AdoptedStreamServerEndpoint(None,1234,address)")
        self.assertEqual(expected.__repr__(),actual)
