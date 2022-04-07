Index: twisted/test/test_process.py
===================================================================
--- twisted/test/test_process.py	(revision 18572)
+++ twisted/test/test_process.py	(working copy)
@@ -289,7 +289,7 @@
         return d.addCallback(processEnded)
 
 
-    def test_wrongArguments(self):
+    def testWrongArguments(self):
         """
         Test invalid arguments to spawnProcess: arguments and environment
         must only contains string or unicode, and not null bytes.
Index: twisted/internet/posixbase.py
===================================================================
--- twisted/internet/posixbase.py	(revision 18572)
+++ twisted/internet/posixbase.py	(working copy)
@@ -268,9 +268,31 @@
 
     # IReactorProcess
 
+    def _checkProcessArgs(self, args, env):
+        """
+        Check for valid arguments and environment to spawnProcess.
+        """
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
+        if env is not None:
+            for key, val in env.iteritems():
+                if not argChecker(key):
+                    raise TypeError("Environment contains a non-string key")
+                if not argChecker(val):
+                    raise TypeError("Environment contains a non-string value")
+
     def spawnProcess(self, processProtocol, executable, args=(),
                      env={}, path=None,
                      uid=None, gid=None, usePTY=0, childFDs=None):
+        self._checkProcessArgs(args, env)
         if platformType == 'posix':
             if usePTY:
                 if childFDs is not None:
Index: twisted/internet/win32eventreactor.py
===================================================================
--- twisted/internet/win32eventreactor.py	(revision 18572)
+++ twisted/internet/win32eventreactor.py	(working copy)
@@ -210,6 +210,7 @@
             raise ValueError(
                 "Custom child file descriptor mappings are unsupported on "
                 "this platform.")
+        self._checkProcessArgs(args, env)
         return Process(self, processProtocol, executable, args, env, path)
 
 
Index: twisted/internet/process.py
===================================================================
--- twisted/internet/process.py	(revision 18572)
+++ twisted/internet/process.py	(working copy)
@@ -266,23 +266,6 @@
         nuances of setXXuid on UNIX: it will assume that either your effective
         or real UID is 0.)
         """
-        # Common check function
-        def argChecker(arg):
-            return isinstance(arg, (str, unicode)) and '\0' not in arg
-
-        # Make a few tests to check input validity
-        if not isinstance(args, (tuple, list)):
-            raise TypeError("Arguments must be a tuple or list")
-        for arg in args:
-            if not argChecker(arg):
-               raise TypeError("Arguments contain a non-string value")
-        if environment is not None:
-            for key, val in environment.iteritems():
-                if not argChecker(key):
-                    raise TypeError("Environment contains a non-string key")
-                if not argChecker(val):
-                    raise TypeError("Environment contains a non-string value")
-
         if not proto:
             assert 'r' not in childFDs.values()
             assert 'w' not in childFDs.values()
