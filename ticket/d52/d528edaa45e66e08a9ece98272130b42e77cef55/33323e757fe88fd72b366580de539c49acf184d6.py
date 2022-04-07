Index: twisted/internet/process.py
===================================================================
--- twisted/internet/process.py	(revision 18372)
+++ twisted/internet/process.py	(working copy)
@@ -266,6 +266,23 @@
         nuances of setXXuid on UNIX: it will assume that either your effective
         or real UID is 0.)
         """
+        # Common check function
+        def argChecker(arg):
+            return isinstance(arg, (str, unicode)) and '\0' not in arg
+
+        # Make a few tests to check input validity
+        if not isinstance(args, (tuple, list)):
+            raise TypeError("Arguments must be a tuple or list")
+        for arg in args:
+            if not argChecker(arg):
+               raise TypeError("Arguments contain a non-string value")
+        if environment is not None:
+            for key, val in environment.items():
+                if not argChecker(key):
+                    raise TypeError("Environment contains a non-string key")
+                if not argChecker(val):
+                    raise TypeError("Environment contains a non-string value")
+
         if not proto:
             assert 'r' not in childFDs.values()
             assert 'w' not in childFDs.values()
Index: twisted/test/test_process.py
===================================================================
--- twisted/test/test_process.py	(revision 18372)
+++ twisted/test/test_process.py	(working copy)
@@ -288,6 +288,30 @@
             self.assertEquals(recvdArgs, args)
         return d.addCallback(processEnded)
 
+    def testWrongArguments(self):
+        """
+        Test invalid arguments to spawnProcess: arguments and environment must
+        only contains string or unicode, and not null bytes.
+        """
+        exe = sys.executable
+        scriptPath = util.sibpath(__file__, "process_tester.py")
+        d = defer.Deferred()
+        p = TestProcessProtocol()
+        p.deferred = d
+        self.assertRaises(TypeError, reactor.spawnProcess, p, exe,
+                          [exe, "-u", scriptPath], env={"foo": 2})
+        self.assertRaises(TypeError, reactor.spawnProcess, p, exe,
+                          [exe, "-u", scriptPath], env={"foo": "egg\0a"})
+        self.assertRaises(TypeError, reactor.spawnProcess, p, exe,
+                          [exe, "-u", scriptPath], env={3: "bar"})
+        self.assertRaises(TypeError, reactor.spawnProcess, p, exe,
+                          [exe, "-u", scriptPath], env={"bar\0foo": "bar"})
+        self.assertRaises(TypeError, reactor.spawnProcess, p, exe,
+                          [exe, 2], env=None)
+        self.assertRaises(TypeError, reactor.spawnProcess, p, exe,
+                          "spam", env=None)
+        self.assertRaises(TypeError, reactor.spawnProcess, p, exe,
+                          [exe, "\0"], env=None)
 
 class TwoProcessProtocol(protocol.ProcessProtocol):
     num = -1
