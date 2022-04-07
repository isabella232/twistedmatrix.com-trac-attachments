"""
Test cases for cddb protocol
"""

from twisted.internet import protocol
from twisted.trial import unittest
import cddbp
import StringIO

class FakeFile(StringIO.StringIO):
    def close(self):
        pass
    
class CDDBPClientTester(cddbp.CDDBPClient):
    def connectionMade(self):
        cddbp.CDDBPClient.connectionMade(self)
        self.empty()
        
    def empty(self):
        self.line = ""
        self.err_line = ""
        self.data = ""
        
    def handleStatus(self, code, line):
        if code in cddbp.successful_codes:
            self.line = line
        elif code in cddbp.multi_line_codes:
            self.multi_line = True
        elif code in cddbp.failure_error_codes:
            self.err_line = line
        elif code in [401, 402, 500, cddbp.NO_MATCH_FOUND,
                      cddbp.DB_ENTRY_CORRUPTED, cddbp.INVALID_DATA,
                      cddbp.SAME_PROTO_LEVEL, cddbp.QUIT_ERROR_CLOSING]:
            self.err_line = line
    
    def parseResponse(self, response):
        pass

class CDDBPClientTestCase(unittest.TestCase):
    tester = f = None
    full_discid = ["f2123610", "16", "150", "29977", "46577", "68970",
                   "85297", "104922", "131622", "150317", "157300",
                   "181212", "208612", "231910", "253045", "273352",
                   "295987", "326627", "4664"]
    cd_data = full_discid[1:]
    discid = full_discid[0]
    full_discid = " ".join(full_discid)
    cd_data = " ".join(cd_data)
    
    def setUp(self):
        self.tester = CDDBPClientTester()
        self.f = FakeFile()
        self.tester.makeConnection(protocol.FileWrapper(self.f))
    
    def checkOK(self, line):
        self.tester.lineReceived(line)
        self.assertEqual(self.tester.line, line)
        self.failIf(self.tester.err_line)
        self.failIf(self.tester.multi_line)

    def checkErr(self, line):
        self.tester.lineReceived(line)
        self.assertEqual(self.tester.err_line, line)
        self.failIf(self.tester.line)
        self.failIf(self.tester.multi_line)
    
    def checkMultiLine(self, line):
        self.tester.lineReceived(line)
        self.assert_(self.tester.multi_line)
    
    def isBufferNotEmpty(self, line):
        self.tester.lineReceived(line)
        self.assertEqual(self.tester.buffer, [line])
    
    def isBufferEmpty(self, line):
        self.tester.lineReceived(line)
        self.failIf(self.tester.buffer)
        self.failIf(self.tester.multi_line)
    
    def checkBuffer(self, line):
        self.isBufferNotEmpty(line)
        line = cddbp.TERMINATING_MARKER
        self.isBufferEmpty(line)

    def testLoginOk(self):
        import time
        code = cddbp.OK_READ_ONLY
        line = "%s foohost CDDBP server v1.0 ready %s" % (code, time.asctime())
        self.tester.lineReceived(line)
        self.checkOK(line)
    
    def testLoginNotAllowed(self):
        line = "%s no connections allowed" % cddbp.CONNECT_PERMISSION_DENIED
        self.tester.lineReceived(line)
        self.checkErr(line)
 
    def testHelloHandshakeSuccessful(self):
        username, host, app, version = "foo", "localhost", "bar", "0.1"
        self.tester.hello(username, host, app, version)
        line = "%s hello and welcome %s@%s running %s %s" %\
            (cddbp.OK,
             username,
             host,
             app, version)
        self.checkOK(line)

    def testHelloHandshakeFailed(self):
        username, host, app, version = "foo", "localhost", "bar", "0.1"
        self.tester.hello(username, host, app, version)
        line = "%s handshake failed" % cddbp.HANDSHAKE_FAILED
        self.checkErr(line)

    def testLscat(self):
        self.tester.lscat()
        code = cddbp.OK_FURTHER_DATA_FOLLOWS
        line = "%s Okay category list follows (until terminating marker)" % code
        self.checkMultiLine(line)
        line = "test"
        self.isBufferNotEmpty(line)
        line = cddbp.TERMINATING_MARKER
        self.isBufferEmpty(line)

    def testQueryExactMatch(self):
        self.tester.query(self.full_discid)
        code = cddbp.EXACT_MATCH
        line = "%s misc f2123610 Common / Like Water For Chocolate" % code
        self.checkOK(line)

    def testQueryMultipleInexactMatches(self):
        self.tester.query(self.full_discid)
        line = "%s close matches found" % cddbp.MULTIPLE_INEXACT_MATCHES
        self.checkMultiLine(line)
        line = "misc f2123610 Common / Like Water For Chocolate"
        self.checkBuffer(line)
        
    testQueryMultipleExactMatches = testQueryMultipleInexactMatches
   
    def testQueryMatchNotFound(self):
        self.tester.query(self.full_discid)
        line = "%s no match found" % cddbp.NO_MATCH_FOUND
        self.checkErr(line)

    def testQueryDBEntryCorrupted(self):
        self.tester.query(self.full_discid)
        line = "%s database entry is corrupt" % cddbp.DB_ENTRY_CORRUPTED
        self.checkErr(line)
    
    def testReadEntryFollows(self):
        self.tester.read("misc", self.discid)
        code = cddbp.OK_FURTHER_DATA_FOLLOWS
        line = "%s OK, CDDB database entry follows" % code
        self.checkMultiLine(line)
        line = "test"
        self.checkBuffer(line)
    
    def testReadMatchNotFound(self):
        self.tester.read("misc", self.discid)
        line = "%s specified CDDB entry not found." % cddbp.NOT_AVAILABLE
        self.checkErr(line)
    
    def testReadServerError(self):
        self.tester.read("misc", self.discid)
        line = "%s server error." % cddbp.SERVER_ERROR
        self.checkErr(line)

    def testReadDBEntryCorrupted(self):
        self.tester.read("misc", self.discid)
        line = "%s server error." % cddbp.DB_ENTRY_CORRUPTED
        self.checkErr(line)
    
    def testDiscidComputed(self):
        self.tester.discid(self.cd_data)
        line = "%s Discid is %s" % (cddbp.OK, self.discid)
        self.checkOK(line)
    
    def testHelp(self):
        self.tester.help()
        code = cddbp.OK_FURTHER_DATA_FOLLOWS
        line = "%s OK, help information follows" % code
        self.checkMultiLine(line)
        line = "test"
        self.checkBuffer(line)
    
    def testHelpNotAvailable(self):
        self.tester.help("quit")
        code = cddbp.NOT_AVAILABLE
        line = "%s No help information available" % code
        self.checkErr(line)
    
    def testMotd(self):
        self.tester.motd()
        code = cddbp.OK_FURTHER_DATA_FOLLOWS
        line = "%s OK, Last modified: 01/02/03 01:02:03 MOTD follows" % code
        self.checkMultiLine(line)
        line = "test"
        self.checkBuffer(line)
    
    def testMotdNotAvailable(self):
        self.tester.motd()
        code = cddbp.NOT_AVAILABLE
        line = "%s No message of the day available" % code
        self.checkErr(line)
    
    def testProtoGet(self):
        self.tester.proto()
        code = cddbp.CURRENT_PROTO_LEVEL
        line = "%s CDDB protocol level: current 1, supported 6" % code
        self.checkOK(line)
    
    def testProtoCorrectSet(self):
        level = "6"
        self.tester.proto(level)
        code = cddbp.OK_PROTO_LEVEL_CHANGED
        line = "%s OK, protocol version now: %s" % (code, level)
        self.checkOK(line)
    
    def testProtoIllegalSet(self):
        self.tester.proto("9")
        code = cddbp.INVALID_DATA
        line = "%s Illegal protocol level." % code
        self.checkErr(line)
    
    def testProtoSameLevel(self):
        level = "1"
        self.tester.proto(level)
        code = cddbp.SAME_PROTO_LEVEL
        line = "%s OK, protocol version now: %s" % (code, level)
        self.checkErr(line)
    
    def testQuitOkClosing(self):
        self.tester.quit()
        code = cddbp.QUIT_OK_CLOSING
        line = "%s foo.bar.com Closing connection.  Goodbye." % code
        self.checkOK(line)
    
    def testQuitErrClosing(self):
        self.tester.quit()
        code = cddbp.QUIT_ERROR_CLOSING
        line = "%s foo.bar.com error, closing connection." % code
        self.checkErr(line)
    
    def testSites(self):
        self.tester.sites()
        code = cddbp.OK_FURTHER_DATA_FOLLOWS
        line = "%s OK, site information follows" % code
        self.checkMultiLine(line)
        line = "test"
        self.checkBuffer(line)
    
    def testSitesNotAvailable(self):
        self.tester.sites()
        code = cddbp.NOT_AVAILABLE
        line = "%s No site information available" % code
        self.checkErr(line)
    
    def testStat(self):
        self.tester.stat()
        code = cddbp.OK_FURTHER_DATA_FOLLOWS
        line = "%s OK, status information follows" % code
        self.checkMultiLine(line)
        line = "test"
        self.checkBuffer(line)
    
    def testVer(self):
        self.tester.ver()
        code = cddbp.OK
        line = "%s fooserver 1.0 Copyright (c) 2004 Spider Man" % code
        self.checkOK(line)
    
    def testVerMultiline(self):
        self.tester.ver()
        code = cddbp.OK_VERSION_INFO_FOLLOWS
        line = "%s OK, Version information follows" % code
        self.checkMultiLine(line)
        line = "test"
        self.checkBuffer(line)

    #def testUnlinkOk(self):
        #self.tester.unlink("misc", self.discid)
        #code = cddbp.OK
        #line = "%s OK, file has been deleted." % code
        #self.checkOK(line)
    
    #def testUnlinkDenied(self):
        #self.tester.unlink("misc", self.discid)
        #code = cddbp.UNLINK_PERMISSION_DENIED
        #line = "%s Permission denied." % code
        #self.checkErr(line)
    
    #def testUnlinkFileAccessFailed(self):
        #self.tester.unlink("misc", self.discid)
        #code = cddbp.FILE_ACCESS_FAILED
        #line = "%s File access failed." % code
        #self.checkErr(line)
    
    #def testUnlinkInvalidCategory(self):
        #self.tester.unlink("misc", self.discid)
        #code = cddbp.INVALID_DATA
        #line = "%s Invalid category: %s" % (code, "misc")
        #self.checkErr(line)
   
    def test500Codes(self):
        self.tester.sendLine("foo bar")
        # since cddbp uses the same code for 3 differents things, testing
        # one or another it's the same
        line = "%s blah blah" % cddbp.UNKOWN_COMMAND
        self.checkErr(line)

class CDDBPServerTester(cddbp.CDDBPServer):
    pass

class CDDBPServerTestCase(unittest.TestCase):
    def testClientLogged(self):
        pass