Index: twisted/test/test_threadpool.py
===================================================================
--- twisted/test/test_threadpool.py	(révision 18384)
+++ twisted/test/test_threadpool.py	(copie de travail)
@@ -66,6 +66,8 @@
         self.assertEquals(len(tp.threads), 7)
         self.assertEquals(tp.min, 7)
         self.assertEquals(tp.max, 20)
+        for thr in tp.threads:
+            self.assertNot(thr._Thread__args)
 
         # check that unpickled threadpool has same number of threads
         s = pickle.dumps(tp)
@@ -129,8 +131,10 @@
         waiter.acquire()
 
         tp = threadpool.ThreadPool(0, 1)
+        self.assertEquals(tp.threads, [])
         tp.callInThread(waiter.release) # before start()
         tp.start()
+        self.assertNot(tp.threads[0]._Thread__args)
 
         try:
             self._waitForLock(waiter)
Index: twisted/python/threadpool.py
===================================================================
--- twisted/python/threadpool.py	(révision 18384)
+++ twisted/python/threadpool.py	(copie de travail)
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
