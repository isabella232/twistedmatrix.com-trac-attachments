"""Test suite for asyncronous I/O support for Windows Console.

For testing I use the low level WriteConsoleInput function that allows
to write directly in the console input queue.
"""

import os, sys
import win32console

from twisted.trial import unittest
from twisted.python import filepath
from twisted.internet import error, defer, protocol, reactor

from twisted.internet import conio, _win32stdio as stdio



def createKeyEvent(char, repeat=1):
    """Create a low level record structure with the given character.
    """
    
    evt = win32console.PyINPUT_RECORDType(win32console.KEY_EVENT)
    evt.KeyDown = True
    evt.Char = char
    evt.RepeatCount = repeat

    return evt


stdin = win32console.GetStdHandle(win32console.STD_INPUT_HANDLE)


class ConInTestCase(unittest.TestCase):
    """Test case for console stdin.
    """

    def tearDown(self):
        conio.stdin.flush()

    def testRead(self):
        data = u"hello\r"
        records = [createKeyEvent(c) for c in data]
        stdin.WriteConsoleInput(records)

        result = conio.stdin.read()
        self.failUnlessEqual(result, "hello\n")

    def testRead2(self):
        """Test two consecutives read.
        """

        def read():
            data = u"hello\r"
            records = [createKeyEvent(c) for c in data]
            stdin.WriteConsoleInput(records)
            
            result = conio.stdin.read()
            self.failUnlessEqual(result, "hello\n")
    
        read()
        read()

    def testReadMultiple(self):
        """Test if repeated characters are handled correctly.
        """

        data = u"hello\r"
        records = [createKeyEvent(c, 3) for c in data]
        stdin.WriteConsoleInput(records)

        result = conio.stdin.read()
        self.failUnlessEqual(result, "hhheeellllllooo\n\n\n")

    def testReadWithDelete(self):
        """Test if deletion is handled correctly.
        """

        data = u"hello" + u"\b" * 5 + u"world\r"
        records = [createKeyEvent(c) for c in data]
        stdin.WriteConsoleInput(records)

        result = conio.stdin.read()
        self.failUnlessEqual(result, "world\n")

    def testDeleteBoundary(self):
        """Test if deletion is handled correctly.
        """

        data = u"h" + "\b\b" + u"w\r"
        records = [createKeyEvent(c) for c in data]
        stdin.WriteConsoleInput(records)

        result = conio.stdin.read()
        self.failUnlessEqual(result, "w\n")

    def testDeleteFullBoundary(self):
        """Test if deletion is handled correctly.
        """

        data = u"h" * 500 + "\b" * 600 + u"w\r"
        records = [createKeyEvent(c) for c in data]
        stdin.WriteConsoleInput(records)

        result = conio.stdin.read()
        self.failUnlessEqual(result, "w\n")

    def testReadWithBuffer(self):
        data = u"hello\r"
        records = [createKeyEvent(c) for c in data]
        stdin.WriteConsoleInput(records)

        result = conio.stdin.read(3)
        self.failUnlessEqual(result, "hel")

        result = conio.stdin.read(3)
        self.failUnlessEqual(result, "lo\n")

    def testReadWouldBlock(self):
        data = u"hello"
        records = [createKeyEvent(c) for c in data]
        stdin.WriteConsoleInput(records)

        self.failUnlessRaises(IOError, conio.stdin.read)

    def testReadWouldBlockBuffer(self):
        data = u"hello"
        records = [createKeyEvent(c) for c in data]
        stdin.WriteConsoleInput(records)

        self.failUnlessRaises(IOError, conio.stdin.read, 3)

    def testIsatty(self):
        self.failUnless(conio.stdin.isatty())

    def testBuffer(self):
        data = u"hello"
        records = [createKeyEvent(c) for c in data]
        stdin.WriteConsoleInput(records)

        try:
            # This will put the data in the accumulation buffer
            conio.stdin.read()
        except IOError:
            pass
        
        self.failUnlessEqual(conio.stdin._buf, list("hello"))

    def testFlush(self):
        data = u"hello\r"
        records = [createKeyEvent(c) for c in data]
        stdin.WriteConsoleInput(records)

        result = conio.stdin.read(3)
        conio.stdin.flush()
        
        self.failIf(conio.stdin.buffer)
        self.failUnlessRaises(IOError, conio.stdin.read, 3)

    def testFlushBuffer(self):
        data = u"hello"
        records = [createKeyEvent(c) for c in data]
        stdin.WriteConsoleInput(records)

        try:
            # This will put the data in the accumulation buffer
            conio.stdin.read()
        except IOError:
            pass

        conio.stdin.flush()
        
        self.failIf(conio.stdin.buffer)
        self.failIf(conio.stdin._buf)
        self.failUnlessRaises(IOError, conio.stdin.read, 3)


class ConInRawTestCase(unittest.TestCase):
    """Test case for console stdin in raw mode.
    """

    def setUp(self):
        conio.stdin.enableRawMode()

    def tearDown(self):
        conio.stdin.flush()
        conio.stdin.enableRawMode(False)

    def testRead(self):
        data = u"hello"
        records = [createKeyEvent(c) for c in data]
        stdin.WriteConsoleInput(records)

        result = conio.stdin.read()
        self.failUnlessEqual(result, "hello")

    
    def testReadMultiple(self):
        data = u"hello"
        records = [createKeyEvent(c, 3) for c in data]
        stdin.WriteConsoleInput(records)

        result = conio.stdin.read()
        self.failUnlessEqual(result, "hhheeellllllooo")

        
    def testReadWithDelete(self):
        data = u"hello" + u'\b' * 5 + u"world"
        records = [createKeyEvent(c) for c in data]
        stdin.WriteConsoleInput(records)

        result = conio.stdin.read()
        self.failUnlessEqual(result, "hello" + '\b' * 5 + "world")

    def testReadWithBuffer(self):
        data = u"hello\r"
        records = [createKeyEvent(c) for c in data]
        stdin.WriteConsoleInput(records)

        result = conio.stdin.read(3)
        self.failUnlessEqual(result, "hel")

        result = conio.stdin.read(3)
        self.failUnlessEqual(result, "lo\n")

    def testFlush(self):
        data = u"hello"
        records = [createKeyEvent(c) for c in data]
        stdin.WriteConsoleInput(records)

        result = conio.stdin.read(3)
        conio.stdin.flush()

        self.failIf(conio.stdin.buffer)
        self.failIf(conio.stdin.read())


class ConOutTestCase(unittest.TestCase):
    """Test case for console stdout.
    Not very much to test, yet.
    """
    
    def testWrite(self):
        data = "hello"
        n = conio.stdout.write(data)
        
        self.failUnlessEqual(n, 5)

    def testWriteUnicode(self):
        data = u"hello"
        n = conio.stdout.write(data)
        
        self.failUnlessEqual(n, 5)

    def testWritelines(self):
        data = ["hello", "world"]
        n = conio.stdout.writelines(data)
        
        self.failUnlessEqual(n, 10)

    def testIsatty(self):
        self.failUnless(conio.stdout.isatty())



class StdIOTestProtocol(protocol.Protocol):
    def __init__(self):
        self.onData = defer.Deferred()

    def dataReceived(self, data):
        self.onData.callback(data)


class StdIOTestCase(unittest.TestCase):
    """Test twisted.internet.stdio support for consoles.
    """
 
    def setUp(self):
        p = StdIOTestProtocol()
        self.stdio = stdio.StandardIO(p)
        self.onData = p.onData

    def tearDown(self):
        self.stdio._pause()
        try:
            self.stdio._stopPolling()
        except error.AlreadyCalled:
            pass
        
        conio.stdin.flush()

    def testRead(self):
        def cb(result):
            self.failUnlessEqual(result, "hello\n")

        data = u"hello\r"
        records = [createKeyEvent(c) for c in data]
        stdin.WriteConsoleInput(records)

        return self.onData.addCallback(cb)
