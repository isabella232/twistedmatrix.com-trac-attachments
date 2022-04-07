Index: web.py
===================================================================
RCS file: /cvs/Twisted/twisted/tap/web.py,v
retrieving revision 1.45
diff -u -r1.45 web.py
--- web.py	31 Jul 2003 13:12:32 -0000	1.45
+++ web.py	6 Aug 2003 23:38:08 -0000
@@ -40,7 +40,9 @@
     optFlags = [["personal", "",
                  "Instead of generating a webserver, generate a "
                  "ResourcePublisher which listens on "
-                 "~/%s" % distrib.UserDirectory.userSocketName]]
+                 "~/%s" % distrib.UserDirectory.userSocketName],
+                 ["disable-tracebacks", "",
+                 "Do not display tracebacks in the browser."]]
 
     longdesc = """\
 This creates a web.tap file that can be used by twistd.  If you specify
@@ -169,6 +171,9 @@
     else:
         site = server.Site(root)
 
+    if config['disable-tracebacks']:
+        site.displayTraceback = False
+        
     if config['personal']:
         import pwd,os
 
