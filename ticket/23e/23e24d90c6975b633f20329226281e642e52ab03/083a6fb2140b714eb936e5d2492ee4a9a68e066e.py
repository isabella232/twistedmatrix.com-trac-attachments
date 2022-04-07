Index: twisted/python/threadpool.py
===================================================================
--- twisted/python/threadpool.py	(révision 18490)
+++ twisted/python/threadpool.py	(copie de travail)
@@ -36,11 +36,10 @@
     a single thread, unless you make a subclass where stop() and
     _startSomeWorkers() are synchronized.
     """
-    __inited = 0
     min = 5
     max = 20
-    joined = 0
-    started = 0
+    joined = False
+    started = False
     workers = 0
     name = None
 
@@ -48,7 +47,8 @@
     currentThread = staticmethod(threading.currentThread)
 
     def __init__(self, minthreads=5, maxthreads=20, name=None):
-        """Create a new threadpool.
+        """
+        Create a new threadpool.
 
         @param minthreads: minimum number of threads in the pool
 
@@ -70,15 +70,16 @@
             self.working = ThreadSafeList()
 
     def start(self):
-        """Start the threadpool.
         """
-        self.joined = 0
-        self.started = 1
+        Start the threadpool.
+        """
+        self.joined = False
+        self.started = True
         # Start some threads.
         self.adjustPoolsize()
 
     def startAWorker(self):
-        self.workers = self.workers + 1
+        self.workers += 1
         name = "PoolThread-%s-%s" % (self.name or id(self), self.workers)
         newThread = self.threadFactory(target=self._worker, name=name)
         self.threads.append(newThread)
@@ -86,7 +87,7 @@
 
     def stopAWorker(self):
         self.q.put(WorkerStop)
-        self.workers = self.workers-1
+        self.workers -= 1
 
     def __setstate__(self, state):
         self.__dict__ = state
@@ -107,8 +108,9 @@
             self.startAWorker()
 
     def dispatch(self, owner, func, *args, **kw):
-        """Dispatch a function to be a run in a thread.
         """
+        Dispatch a function to be a run in a thread.
+        """
         self.callInThread(func,*args,**kw)
 
     def callInThread(self, func, *args, **kw):
@@ -129,17 +131,22 @@
             callback(result)
 
     def dispatchWithCallback(self, owner, callback, errback, func, *args, **kw):
-        """Dispatch a function, returning the result to a callback function.
+        """
+        Dispatch a function, returning the result to a callback function.
 
         The callback function will be called in the thread - make sure it is
         thread-safe.
         """
-        self.callInThread(self._runWithCallback, callback, errback, func, args, kw)
+        self.callInThread(
+            self._runWithCallback, callback, errback, func, args, kw
+        )
 
     def _worker(self):
+        ct = self.currentThread()
+        self.waiters.append(ct)
         o = self.q.get()
-        ct = self.currentThread()
-        while 1:
+        self.waiters.remove(ct)
+        while True:
             if o is WorkerStop:
                 break
             elif o is not None:
@@ -148,7 +155,7 @@
                 try:
                     context.call(ctx, function, *args, **kwargs)
                 except:
-                    context.call(ctx, log.deferr)
+                    context.call(ctx, log.err)
                 self.working.remove(ct)
                 del o, ctx, function, args, kwargs
             self.waiters.append(ct)
@@ -158,12 +165,14 @@
         self.threads.remove(ct)
 
     def stop(self):
-        """Shutdown the threads in the threadpool."""
-        self.joined = 1
+        """
+        Shutdown the threads in the threadpool.
+        """
+        self.joined = True
         threads = copy.copy(self.threads)
-        for thread in range(self.workers):
+        while self.workers:
             self.q.put(WorkerStop)
-            self.workers = self.workers-1
+            self.workers -= 1
 
         # and let's just make sure
         # FIXME: threads that have died before calling stop() are not joined.
@@ -201,7 +210,9 @@
 
 
 class ThreadSafeList:
-    """In Jython 2.1 lists aren't thread-safe, so this wraps it."""
+    """
+    In Jython 2.1 lists aren't thread-safe, so this wraps it.
+    """
 
     def __init__(self):
         self.lock = threading.Lock()
@@ -223,3 +234,4 @@
 
     def __len__(self):
         return len(self.l)
+
Index: twisted/test/test_threadpool.py
===================================================================
--- twisted/test/test_threadpool.py	(révision 18490)
+++ twisted/test/test_threadpool.py	(copie de travail)
@@ -67,7 +67,8 @@
             """
             Mock-thread which is API compatible with L{threading.Thread}.
             """
-            def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, verbose=None):
+            def __init__(self, group=None, target=None, name=None, args=(),
+                         kwargs={}, verbose=None):
                 self.target = target
                 self.args = args
                 self.kwargs = kwargs
@@ -155,17 +156,20 @@
 
             self._waitForLock(waiting)
 
-            self.failIf(actor.failures, "run() re-entered %d times" % (actor.failures,))
+            self.failIf(actor.failures, "run() re-entered %d times" %
+                                        (actor.failures,))
         finally:
             tp.stop()
 
 
     def testDispatch(self):
-        return self._threadpoolTest(lambda tp, actor: tp.dispatch(actor, actor.run))
+        return self._threadpoolTest(
+            lambda tp, actor: tp.dispatch(actor, actor.run))
 
 
     def testCallInThread(self):
-        return self._threadpoolTest(lambda tp, actor: tp.callInThread(actor.run))
+        return self._threadpoolTest(
+            lambda tp, actor: tp.callInThread(actor.run))
 
 
     def testExistingWork(self):
@@ -197,6 +201,11 @@
 
 
     def testRace(self):
+        """
+        Test a race condition: ensure that actions run in the pool synchronize
+        with actions run in the main thread.
+        """
+        self.threadpool.adjustPoolsize(minthreads=4)
         self.threadpool.callInThread(self.event.set)
         self.event.wait()
         self.event.clear()
@@ -210,6 +219,9 @@
 
 
     def testSingleThread(self):
+        """
+        Test that some linear load on the pool keeps the thread count low.
+        """
         # Ensure no threads running
         self.assertEquals(self.threadpool.workers, 0)
 
