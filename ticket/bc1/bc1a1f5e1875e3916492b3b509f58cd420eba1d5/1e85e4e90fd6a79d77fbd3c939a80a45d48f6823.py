# Copyright (c) 2006 Twisted Matrix Laboratories.
# See LICENSE for details.

import os, sys
import win32api, win32console, win32con

from twisted.trial import unittest
from twisted.python import filepath
from twisted.internet import error, defer, protocol, reactor

import _win32stdio as stdio



def createKeyEvent(char, repeat=1):
    evt = win32console.PyINPUT_RECORDType(win32console.KEY_EVENT)
    evt.KeyDown = True
    evt.Char = char
    evt.RepeatCount = repeat

    return evt


stdin = win32console.GetStdHandle(win32console.STD_INPUT_HANDLE)


class ConIOTestProtocol(protocol.Protocol):
    def __init__(self):
        self.onData = defer.Deferred()

    def dataReceived(self, data):
        self.onData.callback(data)


class ConIOTestCase(unittest.TestCase):
    def setUp(self):
        p = ConIOTestProtocol()
        self.stdio = stdio.StandardIO(p)
        self.onData = p.onData

    def tearDown(self):
        self.stdio._pause()
        try:
            self.stdio._stopPolling()
        except error.AlreadyCalled:
            pass
        
    def testRead(self):
        def cb(result):
            self.failUnlessEqual(result, "hello\r\n")

        data = u"hello\r"
        records = [createKeyEvent(c) for c in data]

        stdin.WriteConsoleInput(records)
        return self.onData.addCallback(cb)
    
    def testReadMultiple(self):
        def cb(result):
            self.failUnlessEqual(result, "hhheeellllllooo\r\n\r\n\r\n")

        data = u"hello\r"
        records = [createKeyEvent(c, 3) for c in data]

        stdin.WriteConsoleInput(records)
        return self.onData.addCallback(cb)
        
    def testReadWithDelete(self):
        def cb(result):
            self.failUnlessEqual(result, "world\r\n")
            
        data = u"hello" + u"\b" * 5 + u"world\r"
        records = [createKeyEvent(c) for c in data]

        stdin.WriteConsoleInput(records)
        return self.onData.addCallback(cb)

    def testDeleteBoundary(self):
        def cb(result):
            self.failUnlessEqual(result, "w\r\n")
            
        data = u"h" + "\b\b" + u"w\r"
        records = [createKeyEvent(c) for c in data]

        stdin.WriteConsoleInput(records)
        return self.onData.addCallback(cb)

    def testDeleteFullBoundary(self):
        def cb(result):
            self.failUnlessEqual(result, "w\r\n")
            
        data = u"h" * 500 + "\b" * 600 + u"w\r"
        records = [createKeyEvent(c) for c in data]

        stdin.WriteConsoleInput(records)
        return self.onData.addCallback(cb)

    
class ConIORawTestCase(unittest.TestCase):
    def setUp(self):
        p = ConIOTestProtocol()
        self.stdio = stdio.StandardIO(p)
        self.stdio.stdin.enableRawMode()
        self.onData = p.onData

    def tearDown(self):
        self.stdio.stdin.enableRawMode(False)

        self.stdio._pause()
        try:
            self.stdio._stopPolling()
        except error.AlreadyCalled:
            pass
        
    def testRead(self):
        def cb(result):
            self.failUnlessEqual(result, "hello")

        data = u"hello"
        records = [createKeyEvent(c) for c in data]

        stdin.WriteConsoleInput(records)
        return self.onData.addCallback(cb)
    
    def testReadMultiple(self):
        def cb(result):
            self.failUnlessEqual(result, "hhheeellllllooo")

        data = u"hello"
        records = [createKeyEvent(c, 3) for c in data]

        stdin.WriteConsoleInput(records)
        return self.onData.addCallback(cb)
        
    def testReadWithDelete(self):
        def cb(result):
            self.failUnlessEqual(result, "hello\b\b\b\b\bworld")
            
        data = u"hello" + u"\b" * 5 + u"world"
        records = [createKeyEvent(c) for c in data]

        stdin.WriteConsoleInput(records)
        return self.onData.addCallback(cb)
       

class ConIORawSwitchTestCase(unittest.TestCase):
    def setUp(self):
        p = ConIOTestProtocol()
        self.stdio = stdio.StandardIO(p)
        self.onData = p.onData

    def tearDown(self):
        self.stdio.stdin.enableRawMode(False)

        self.stdio._pause()
        try:
            self.stdio._stopPolling()
        except error.AlreadyCalled:
            pass

    def testEnableRawMode(self):
        def cb(result):
            self.failUnlessEqual(result, "hello")

        data = u"hello"
        records = [createKeyEvent(c) for c in data]

        stdin.WriteConsoleInput(records)
        self.stdio.stdin.enableRawMode()
        
        return self.onData.addCallback(cb)
