--- postfix.py.orig     Tue Jul 25 00:57:49 2006
+++ postfix.py  Tue Jul 25 01:08:13 2006
@@ -48,6 +48,7 @@
     def sendCode(self, code, message=''):
         "Send an SMTP-like code with a message."
         self.sendLine('%3.3d %s' % (code, message or ''))
+        self.resetTimeout()
 
     def lineReceived(self, line):
         self.resetTimeout()