Index: twisted/protocols/ftp.py
===================================================================
--- twisted/protocols/ftp.py	(revision 24235)
+++ twisted/protocols/ftp.py	(working copy)
@@ -2404,6 +2404,50 @@
 
     stor = storeFile
 
+    def rename(self, pathFrom, pathTo):
+        """
+        Rename a file.
+
+        This method issues the 'RNFR, RNTO' command sequence.
+        @param: pathFrom: the absolute path to the file to be renamed
+        @param: pathTo: the absolute path to rename the file to.
+        @return: A list of L{deferred}s. Add your callbacks to the last one. 
+        """
+
+        cmds = ['RNFR ' + self.escapePath(pathFrom),
+                'RNTO ' + self.escapePath(pathTo)]
+        d1 = self.queueStringCommand(cmds[0])
+        d2 = self.queueStringCommand(cmds[1])
+
+        def RNFR_pass(result):
+            return d2
+        def RNFR_fail(failure):
+            self.popCommandQueue()
+            return d2.errback(failure)
+        d1.addCallbacks(RNFR_pass, RNFR_fail)
+        return d2
+
+    def makeDirectory(self, path):
+        """
+        Make a directory
+
+        This method issues the MKD command.
+        @param path: The path to the directory to create.
+        @return a L{Deferred} with a Failure if the command fails.
+        """
+        def cbCheckRes(result):
+            try:
+                # The only valid code is 257 or 250
+                code = int(result[0].split(' ', 1)[0])
+                if code == 250 or code == 257:
+                    return True
+                else:
+                    raise ValueError
+            except (IndexError, ValueError), e:
+                return failure.Failure(CommandFailed(result))
+            return defer.fail(result)
+        return self.queueStringCommand('MKD ' + self.escapePath(path)).addCallback(cbCheckRes)
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
@@ -1351,7 +1352,103 @@
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
+    def testRenameFromToFailingOnFirstError(self):
+        """
+        Test renaming a file that does not exist.
+        """
+        self._testLogin()
+        d2 = self.client.rename("/spam", "/ham")
+        self.assertEquals(self.transport.value(), 'RNFR /spam\r\n')
+        self.transport.clear()
+        self.client.lineReceived('550 Requested file unavailable.\r\n')
+        # the client disconnects on first error and thus clears the action queue
+        self.assertEquals(self.client.actionQueue, [])
+        self.assertFailure(d2, ftp.CommandFailed)
+        return d2
+
+    def testRenameFromToFailingOnRenameTo(self):
+        """
+        Test renaming a file to an impossible path
+        """
+        self._testLogin()
+        d2 = self.client.rename("/spam", "/ham")
+        self.assertEquals(self.transport.value(), 'RNFR /spam\r\n')
+        def assertFail(result):
+            self.assertTrue(isinstance(result, failure.Failure))
+        d2.addErrback(assertFail)
+        self.transport.clear()
+        self.client.lineReceived('350 Requested file action pending further information.\r\n')
+        self.assertEquals(self.transport.value(), 'RNTO /ham\r\n')
+        self.client.lineReceived('550 Requested file unavailable.\r\n')
+        self.assertEquals(self.client.actionQueue, [])
+        return d2
+
+
+    def test_makeDirectory(self):
+        """
+        Sunshine test of the makeDirectory method.
+
+        L{ftp.FTPClient.makeDirectory} should return a Deferred.
+        """
+        self._testLogin()
+        def cbMakeDir(res):
+            self.assertEqual(res, True)
+        d = self.client.makeDirectory("/spam")
+        self.assertEquals(self.transport.value(), 'MKD /spam\r\n')
+        self.client.lineReceived('257 "/spam" created.')
+        self.assertEquals(self.client.actionQueue, [])
+        return d.addCallback(cbMakeDir)
+
+    def test_makeDirectoryCode250(self):
+        """
+        It seems that a server may return 250 instead of 257. 
+        This test checks that that is ok.
+        L{ftp.FTPClient.makeDirectory} should return a Deferred.
+        """
+        self._testLogin()
+        def cbMakeDir(res):
+            self.assertEqual(res, True)
+        d = self.client.makeDirectory("/spam")
+        self.assertEquals(self.transport.value(), 'MKD /spam\r\n')
+        self.client.lineReceived('250 Requested file action okay, completed.')
+        self.assertEquals(self.client.actionQueue, [])
+        return d.addCallback(cbMakeDir)
+
+
+    def test_makeDirectoryFail(self):
+        """
+        Sunshine test of the makeDirectory method.
+
+        L{ftp.FTPClient.makeDirectory} should return a Deferred.
+        """
+        self._testLogin()
+        def cbFail(result):
+            self.assertTrue(isinstance(result, failure.Failure))
+        d = self.client.makeDirectory("/spam")
+        self.assertEquals(self.transport.value(), 'MKD /spam\r\n')
+        self.client.lineReceived('550 PERMISSION DENIED')
+        self.assertEquals(self.client.actionQueue, [])
+        return d.addErrback(cbFail)
+
+
     def test_getDirectory(self):
         """
         Test the getDirectory method.
