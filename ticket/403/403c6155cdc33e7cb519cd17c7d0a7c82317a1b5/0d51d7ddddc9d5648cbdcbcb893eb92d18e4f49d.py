from twisted.protocols import basic

result = ""

class DummyTransport:

    def loseConnection(self):
        return "Closed connection"

class MyNetstringReceiver(basic.NetstringReceiver):
    """>>> nsr = MyNetstringReceiver()
       >>> nsr.transport = DummyTransport()
       >>> nsr.dataReceived('1:a,')
       |a|
       >>> nsr.dataReceived('2:aa,')
       |aa|
       >>> nsr.dataReceived('3:aaa,')
       |aaa|
       >>> nsr.dataReceived('3:aa,')
       NetstringParseError occurred
       >>> nsr.dataReceived('3aaa')
       NetstringParseError occurred
       >>> nsr.dataReceived('1:a,a')
       NetstringParseError occurred
       >>> nsr.dataReceived('aaa')
       NetstringParseError occurred
       >>> nsr.dataReceived('0:,')
       ||
       >>> nsr.dataReceived('4:aa')
       >>> nsr.dataReceived('aa,')
       |aaaa|
       >>> nsr._readerState
       0
       """

    def stringReceived(self, data):
        print "|%s|" % data

if __name__ == "__main__":
    import doctest
    doctest.testmod()
