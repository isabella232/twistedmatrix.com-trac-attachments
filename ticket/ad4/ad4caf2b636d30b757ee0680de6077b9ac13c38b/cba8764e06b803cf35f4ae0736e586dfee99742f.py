diff --git a/twisted/web2/filter/gzip.py b/twisted/web2/filter/gzip.py
index 5d6de81..4140b91 100644
--- a/twisted/web2/filter/gzip.py
+++ b/twisted/web2/filter/gzip.py
@@ -55,7 +55,11 @@ def gzipfilter(request, response):
     
     # FIXME: make this a more flexible matching scheme
     mimetype = response.headers.getHeader('content-type')
-    if not mimetype or mimetype.mediaType != 'text':
+    if not mimetype or \
+            (mimetype.mediaType != 'text' \
+                 and 'javascript' not in mimetype.mediaSubtype \
+                 and 'xml' not in mimetype.mediaSubtype \
+                 and 'sgml' not in mimetype.mediaSubtype):
         return response
     
     # Make sure to note we're going to return different content depending on
