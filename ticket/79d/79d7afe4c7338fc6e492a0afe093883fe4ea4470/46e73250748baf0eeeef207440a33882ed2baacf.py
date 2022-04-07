from StringIO import StringIO
from twisted.trial import unittest
from twisted.web2.channel import fastcgi

class FastCGIInfiniteLoopTestCase(unittest.TestCase):
    def testInfiniteLoopOnWrite(self):
        data = 'x'*(fastcgi.FCGI_MAX_PACKET_LEN+1)
        r = fastcgi.FastCGIChannelRequest()
        r.transport = StringIO()
        r.write(data)
        self.assertEquals('xxx', r.transport.getvalue()[8:11])
