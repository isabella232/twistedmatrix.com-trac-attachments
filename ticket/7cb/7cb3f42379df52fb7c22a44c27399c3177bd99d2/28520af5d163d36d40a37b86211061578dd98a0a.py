Index: imap4.py
===================================================================
--- imap4.py	(revision 16040)
+++ imap4.py	(working copy)
@@ -364,9 +364,16 @@
             names = parseNestedParens(L)
             N = len(names)
             if (N >= 1 and names[0] in self._1_RESPONSES or
-                N >= 2 and names[1] in self._2_RESPONSES or
                 N >= 2 and names[0] == 'OK' and isinstance(names[1], types.ListType) and names[1][0] in self._OK_RESPONSES):
                 send.append(L)
+            elif N >= 3 and names[1] in self._2_RESPONSES:
+                if isinstance(names[2], types.ListType) and len(names[2]) >= 1 and \
+                   names[2][0] == 'FLAGS' and 'FLAGS' not in self.args:
+                    unuse.append(L)
+                else:
+                    send.append(L)
+            elif N >= 2 and names[1] in self._2_RESPONSES:
+                send.append(L)
             else:
                 unuse.append(L)
         d, self.defer = self.defer, None
