Index: twisted/protocols/ftp.py
===================================================================
--- twisted/protocols/ftp.py	(revision 24235)
+++ twisted/protocols/ftp.py	(working copy)
@@ -2404,6 +2404,27 @@
 
     stor = storeFile
 
+    def rename(self, pathFrom, pathTo):
+        """
+        Rename a file.
+
+        This method issues the 'RNFR, RNTO' command sequence.
+        @param: pathFrom: the absolute path to the file to be renamed
+        @param: pathTo: the absolute path to rename the file to.
+        @return: A list of L{deferrend}s. Add your callbacks to the last one. 
+        """
+
+        cmds = ['RNFR ' + self.escapePath(pathFrom),
+                'RNTO ' + self.escapePath(pathTo)]
+        d1 = self.queueStringCommand(cmds[0])
+        d2 = self.queueStringCommand(cmds[1])
+
+        def RNFR_pass(result):
+            return d2
+        d1.addCallbacks(RNFR_pass, self.fail)
+        return d2
+        #return defer.gatherResults([d1.addCallbacks(RNFR_pass, RNFR_fail), d2])
+
     def list(self, path, protocol):
         """
         Retrieve a file listing into the given protocol instance.
Index: twisted/test/test_ftp.py
===================================================================
--- twisted/test/test_ftp.py	(revision 24235)
+++ twisted/test/test_ftp.py	(working copy)
@@ -1064,6 +1064,7 @@
         return defer.gatherResults([d1, d2])
 
 
+
     def test_passiveLIST(self):
         """
         Test the LIST command.
@@ -1351,7 +1352,25 @@
         self.client.lineReceived('252 I do what I want !')
         return d
 
+    def testRenameFromTo(self):
+        """
+        Test renaming a file.
 
+        L{ftp.FTPClient.rename} should return a deferred which fires after a successfull
+        RNFR, RNTO sequece to the server.
+        """
+        self._testLogin()
+        def cbFinish(result):
+            self.assertEquals(self.transport.value(), 'RNTO /ham\r\n')
+        d2 = self.client.rename("/spam", "/ham")
+        d2.addCallback(cbFinish)
+        self.assertEquals(self.transport.value(), 'RNFR /spam\r\n')
+        self.transport.clear()
+        self.client.lineReceived('350 Requested file action pending further information.\r\n')
+        self.client.lineReceived('250 Requested File Action Completed OK')
+        return d2
+
+
     def test_getDirectory(self):
         """
         Test the getDirectory method.
