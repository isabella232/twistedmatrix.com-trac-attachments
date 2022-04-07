Index: twisted/conch/test/test_recvline.py
===================================================================
--- twisted/conch/test/test_recvline.py	(revision 18372)
+++ twisted/conch/test/test_recvline.py	(working copy)
@@ -3,15 +3,12 @@
 # See LICENSE for details.
 
 import sys, os
-from pprint import pformat
 
-from zope.interface import implements
-
 from twisted.conch.insults import insults
 from twisted.conch import recvline
 
-from twisted.python import log, reflect, components
-from twisted.internet import defer, error, task
+from twisted.python import reflect, components
+from twisted.internet import defer, error
 from twisted.trial import unittest
 from twisted.cred import portal
 from twisted.test.proto_helpers import StringTransport
@@ -381,12 +378,6 @@
                 " != " +
                 str(expectedLines[max(0, i-1):i+1]))
 
-    def _test(self, s, lines):
-        self._testwrite(s)
-        def asserts(ignored):
-            self._assertBuffer(lines)
-        return defer.maybeDeferred(self._emptyBuffers).addCallback(asserts)
-
     def _trivialTest(self, input, output):
         done = self.recvlineClient.expect("done")
 
@@ -439,9 +430,6 @@
     def _testwrite(self, bytes):
         self.sshClient.write(bytes)
 
-    def _emptyBuffers(self):
-        pass
-
 from twisted.conch.test import test_telnet
 
 class TestInsultsClientProtocol(insults.ClientProtocol,
@@ -481,10 +469,6 @@
     def _testwrite(self, bytes):
         self.telnetClient.write(bytes)
 
-    def _emptyBuffers(self):
-        self.clientTransport.clearBuffer()
-        self.serverTransport.clearBuffer()
-
 try:
     from twisted.conch import stdio
 except ImportError:
@@ -548,11 +532,6 @@
     def _testwrite(self, bytes):
         self.clientTransport.write(bytes)
 
-    def _emptyBuffers(self):
-        from twisted.internet import reactor
-        for i in range(100):
-            reactor.iterate(0.01)
-
 class RecvlineLoopbackMixin:
     serverProtocol = EchoServer
 
@@ -612,8 +591,6 @@
              "home line",
              ">>> done"])
 
-        return done.addCallback(finished)
-
     def testEnd(self):
         return self._trivialTest(
             "end " + left * 4 + end + "line\ndone",
