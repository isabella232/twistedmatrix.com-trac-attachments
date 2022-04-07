Index: test_imap.py
===================================================================
--- test_imap.py	(revision 16040)
+++ test_imap.py	(working copy)
@@ -1659,7 +1659,56 @@
 
         self.server.connectionLost(error.ConnectionDone("Connection done."))
 
+    def testUnsolicitedResponseMixedWithSolicitedResponse(self):
 
+        class StillSimplerClient(imap4.IMAP4Client):
+            events = []
+            def flagsChanged(self, newFlags):
+                self.events.append(['flagsChanged', newFlags])
+
+        transport = StringTransport()
+        c = StillSimplerClient()
+        c.makeConnection(transport)
+        c.lineReceived('* OK [IMAP4rev1]')
+
+        def login():
+            d = c.login('blah', 'blah')
+            c.dataReceived('0001 OK LOGIN\r\n')
+            return d
+        def select():
+            d = c.select('inbox')
+            c.lineReceived('0002 OK SELECT')
+            return d
+        def fetch():
+            d = c.fetchSpecific('1:*',
+                headerType='HEADER.FIELDS',
+                headerArgs=['SUBJECT'])
+            c.dataReceived('* 1 FETCH (BODY[HEADER.FIELDS ("SUBJECT")] {38}\r\n')
+            c.dataReceived('Subject: Suprise for your woman...\r\n')
+            c.dataReceived('\r\n')
+            c.dataReceived(')\r\n')
+            c.dataReceived('* 1 FETCH (FLAGS (\Seen))\r\n')
+            c.dataReceived('* 2 FETCH (BODY[HEADER.FIELDS ("SUBJECT")] {75}\r\n')
+            c.dataReceived('Subject: What you been doing. Order your meds here . ,. handcuff madsen\r\n')
+            c.dataReceived('\r\n')
+            c.dataReceived(')\r\n')
+            c.dataReceived('0003 OK FETCH completed\r\n')
+            return d
+        def test(res):
+            print "HERE"
+            self.assertEquals(res, {
+                1: [['BODY', ['HEADER.FIELDS', ['SUBJECT']],
+                    'Subject: Suprise for your woman...\r\n\r\n']],
+                2: [['BODY', ['HEADER.FIELDS', ['SUBJECT']],
+                    'Subject: What you been doing. Order your meds here . ,. handcuff madsen\r\n\r\n']]
+            })
+
+            self.assertEquals(c.events, [['flagsChanged', {1: ['\\Seen']}]])
+
+        login().addCallback(strip(select)
+            ).addCallback(strip(fetch)
+            ).addCallback(test)
+
 class FakeyServer(imap4.IMAP4Server):
     state = 'select'
     timeout = None
