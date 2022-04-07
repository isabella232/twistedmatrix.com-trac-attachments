Index: twisted/internet/process.py
===================================================================
--- twisted/internet/process.py	(revision 18372)
+++ twisted/internet/process.py	(working copy)
@@ -266,6 +266,18 @@
         nuances of setXXuid on UNIX: it will assume that either your effective
         or real UID is 0.)
         """
+        if not isinstance(args, (tuple, list)):
+            raise TypeError("Arguments must be a tuple or list")
+        for arg in args:
+            if not isinstance(arg, (str, unicode)):
+               raise TypeError("Arguments contain a non-string value")
+        if environment is not None:
+            for key, val in environment.items():
+                if not isinstance(key, (str, unicode)):
+                    raise TypeError("Environment contains a non-string key")
+                if not isinstance(val, (str, unicode)):
+                    raise TypeError("Environment contains a non-string value")
+
         if not proto:
             assert 'r' not in childFDs.values()
             assert 'w' not in childFDs.values()
Index: twisted/test/test_process.py
===================================================================
--- twisted/test/test_process.py	(revision 18372)
+++ twisted/test/test_process.py	(working copy)
@@ -288,6 +288,22 @@
             self.assertEquals(recvdArgs, args)
         return d.addCallback(processEnded)
 
+    def testWrongArguments(self):
+        """
+        Test invalid arguments to spawnProcess: arguments and environment must
+        only contains string or unicode.
+        """
+        exe = sys.executable
+        scriptPath = util.sibpath(__file__, "process_tester.py")
+        d = defer.Deferred()
+        p = TestProcessProtocol()
+        p.deferred = d
+        self.assertRaises(TypeError, reactor.spawnProcess, p, exe,
+                          [exe, "-u", scriptPath], env={"foo": 2})
+        self.assertRaises(TypeError, reactor.spawnProcess, p, exe,
+                          [exe, "-u", scriptPath], env={3: "bar"})
+        self.assertRaises(TypeError, reactor.spawnProcess, p, exe,
+                          [exe, 2], env=None)
 
 class TwoProcessProtocol(protocol.ProcessProtocol):
     num = -1
