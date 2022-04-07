import memcache

from twisted.trial import unittest
from twisted.test.proto_helpers import StringTransportWithDisconnection

class Bean(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class MemCacheTestCase(unittest.TestCase):
    def setUp(self):
        self.proto = memcache.MemCacheProtocol()
        self.transport = StringTransportWithDisconnection()
        self.transport.protocol = self.proto
        self.proto.makeConnection(self.transport)

    def test_get(self):
        def cb(res):
            self.assertEquals(res, "bar")
        d = self.proto.get("foo")
        d.addCallback(cb)
        self.proto.dataReceived("VALUE foo 0 3\r\nbar\r\nEND\r\n")
        return d

    def test_emptyGet(self):
        def cb(res):
            self.assertEquals(res, None)
        d = self.proto.get("foo")
        d.addCallback(cb)
        self.proto.dataReceived("END\r\n")
        return d

    def test_set(self):
        def cb(res):
            self.assert_(res)
        d = self.proto.set("foo", "bar")
        d.addCallback(cb)
        self.proto.dataReceived("STORED\r\n")
        return d

    def test_add(self):
        def cb(res):
            self.assert_(res)
        d = self.proto.add("foo", "bar")
        d.addCallback(cb)
        self.proto.dataReceived("STORED\r\n")
        return d

    def test_replace(self):
        def cb(res):
            self.assert_(res)
        d = self.proto.replace("foo", "bar")
        d.addCallback(cb)
        self.proto.dataReceived("STORED\r\n")
        return d

    def test_errorAdd(self):
        def cb(res):
            self.assertFalse(res)
        d = self.proto.add("foo", "bar")
        d.addCallback(cb)
        self.proto.dataReceived("NOT STORED\r\n")
        return d

    def test_errorReplace(self):
        def cb(res):
            self.assertFalse(res)
        d = self.proto.replace("foo", "bar")
        d.addCallback(cb)
        self.proto.dataReceived("NOT STORED\r\n")
        return d

    def test_delete(self):
        def cb(res):
            self.assert_(res)
        d = self.proto.delete("bar")
        d.addCallback(cb)
        self.proto.dataReceived("DELETED\r\n")
        return d

    def test_errorDelete(self):
        def cb(res):
            self.assertFalse(res)
        d = self.proto.delete("bar")
        d.addCallback(cb)
        self.proto.dataReceived("NOT FOUND\r\n")
        return d

    def test_increment(self):
        def cb(res):
            self.assertEquals(res, 4)
        d = self.proto.incr("foo")
        d.addCallback(cb)
        self.proto.dataReceived("4\r\n")
        return d

    def test_decrement(self):
        def cb(res):
            self.assertEquals(res, 5)
        d = self.proto.decr("foo")
        d.addCallback(cb)
        self.proto.dataReceived("5\r\n")
        return d

    def test_stats(self):
        def cb(res):
            self.assertEquals(res, {"foo": "bar"})
        d = self.proto.stats()
        d.addCallback(cb)
        self.proto.dataReceived("STAT foo bar\r\nEND\r\n")
        return d

    def test_version(self):
        def cb(res):
            self.assertEquals(res, "1.1")
        d = self.proto.version()
        d.addCallback(cb)
        self.proto.dataReceived("VERSION 1.1\r\n")
        return d

    def test_flushAll(self):
        def cb(res):
            self.assert_(res)
        d = self.proto.flushAll()
        d.addCallback(cb)
        self.proto.dataReceived("OK\r\n")
        return d

    def test_strSet(self):
        def cb(res):
            self.assert_(res)
        a = "eggspamm"
        d = self.proto.set("foo", a)
        d.addCallback(cb)
        self.proto.dataReceived("STORED\r\n")
        return d

    def test_marshalSet(self):
        def cb(res):
            self.assert_(res)
        a = [3, 'r', 5]
        d = self.proto.set("foo", a)
        d.addCallback(cb)
        self.proto.dataReceived("STORED\r\n")
        return d

    def test_complexSet(self):
        def cb(res):
            self.assert_(res)
        a = Bean(foo="bar")
        d = self.proto.set("foo", a)
        d.addCallback(cb)
        self.proto.dataReceived("STORED\r\n")
        return d

    def test_strGet(self):
        def cb(res):
            self.assertEquals(res, "spamegg")
        s = "spamegg"
        d = self.proto.get("foo")
        d.addCallback(cb)
        self.proto.dataReceived("VALUE foo 32 %s\r\n%s\r\nEND\r\n" % (len(s), s))
        return d

    def test_marshalGet(self):
        def cb(res):
            self.assertEquals(res, [3, 'r', 5])
        a = [3, 'r', 5]
        d = self.proto.get("foo")
        d.addCallback(cb)
        s = memcache.marshal.dumps(a)
        self.proto.dataReceived("VALUE foo 16 %s\r\n%s\r\nEND\r\n" % (len(s), s))
        return d

    def test_pickleGet(self):
        def cb(res):
            self.assertEquals(res.foo, "bar")
        a = Bean(foo="bar")
        d = self.proto.get("foo")
        d.addCallback(cb)
        s = memcache.pickle.dumps(a)
        self.proto.dataReceived("VALUE foo 1 %s\r\n%s\r\nEND\r\n" % (len(s), s))
        return d

    def test_ntGet(self):
        def cb(res):
            self.assertEquals(res, 12)
            self.assert_(isinstance(res, int))
        d = self.proto.get("foo")
        d.addCallback(cb)
        self.proto.dataReceived("VALUE foo 2 2\r\n%d\r\nEND\r\n" % 12)
        return d

    def test_longGet(self):
        def cb(res):
            self.assertEquals(res, 12)
            self.assert_(isinstance(res, long))
        d = self.proto.get("foo")
        d.addCallback(cb)
        self.proto.dataReceived("VALUE foo 4 2\r\n%d\r\nEND\r\n" % 12)
        return d

    def test_bigSet(self):
        def cb(res):
            self.assert_(res)
        b = "X" * 200000
        a = Bean(foo=b)
        d = self.proto.set("foo", a)
        d.addCallback(cb)
        self.proto.dataReceived("STORED\r\n")
        return d

    def test_bigGet(self):
        b = "X" * 200000
        def cb(res):
            self.assertEquals(res.foo, b)
        a = Bean(foo=b)
        d = self.proto.get("foo")
        d.addCallback(cb)
        s = memcache.pickle.dumps(a)
        self.proto.dataReceived("VALUE foo 1 %s\r\n%s\r\nEND\r\n" % (len(s), s))
        return d


