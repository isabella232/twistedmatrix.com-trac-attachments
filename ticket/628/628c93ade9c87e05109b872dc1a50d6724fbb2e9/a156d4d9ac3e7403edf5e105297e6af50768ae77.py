--- trunk/twisted/internet/defer.py	2006-05-15 20:44:33.000000000 -0700
+++ EAS/defer-chainDeferred_docstring.py	2006-06-13 11:31:03.000000000 -0700
@@ -213,7 +213,17 @@
         """Chain another Deferred to this Deferred.
 
         This method adds callbacks to this Deferred to call d's callback or
-        errback, as appropriate."""
+        errback, as appropriate. It is merely a shorthand way of performing the
+        following::
+
+            self.addCallbacks(d.callback, d.errback)
+
+        When you chain a deferred d2 to another deferred d1 with
+        d1.chainDeferred(d2), you are making d2 participate in the callback
+        chain of d1. Thus any event that fires d1 will also fire d2. However,
+        the converse is B{not} true; you can still fire d2 and it will not
+        affect d1.
+        """
         return self.addCallbacks(d.callback, d.errback)
 
     def callback(self, result):
