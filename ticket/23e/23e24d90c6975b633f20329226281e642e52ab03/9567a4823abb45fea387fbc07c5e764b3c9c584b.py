Index: twisted/python/threadpool.py
===================================================================
--- twisted/python/threadpool.py	(revision 17293)
+++ twisted/python/threadpool.py	(working copy)
@@ -77,11 +77,7 @@
     def startAWorker(self):
         self.workers = self.workers + 1
         name = "PoolThread-%s-%s" % (self.name or id(self), self.workers)
-        try:
-            firstJob = self.q.get(0)
-        except Queue.Empty:
-            firstJob = None
-        newThread = threading.Thread(target=self._worker, name=name, args=(firstJob,))
+        newThread = threading.Thread(target=self._worker, name=name)
         self.threads.append(newThread)
         newThread.start()
 
@@ -100,9 +96,10 @@
         return state
 
     def _startSomeWorkers(self):
+        s = self.q.qsize()
         while (
             self.workers < self.max and # Don't create too many
-            len(self.waiters) < self.q.qsize() # but create enough
+            len(self.threads) < s # but create enough
             ):
             self.startAWorker()
 
@@ -136,7 +133,8 @@
         """
         self.callInThread(self._runWithCallback, callback, errback, func, args, kw)
 
-    def _worker(self, o):
+    def _worker(self):
+        o = self.q.get()
         ct = threading.currentThread()
         while 1:
             if o is WorkerStop:
