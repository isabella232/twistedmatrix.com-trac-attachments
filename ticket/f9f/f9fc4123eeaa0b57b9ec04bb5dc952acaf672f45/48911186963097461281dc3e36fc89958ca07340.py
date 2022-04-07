class TestInt8(TestMixin, basic.Int8StringReceiver):
    MAX_LENGTH = 50

class Int8TestCase(unittest.TestCase, LPTestCaseMixin):

    protocol = TestInt8
    strings = ["a", "b" * 16]
    partial_strings = ["\x01", ""]

    def testPartial(self):
        for s in self.partial_strings:
            r = self.getProtocol()
            r.MAX_LENGTH = 99999999
            for c in s:
                r.dataReceived(c)
            self.assertEquals(r.received, [])

    def testReceive(self):
        r = self.getProtocol()
        for s in self.strings:
            for c in struct.pack("!h",len(s))+s:
                r.dataReceived(c)
        self.assertEquals(r.received, self.strings)
