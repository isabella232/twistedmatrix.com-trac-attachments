# Copyright (c) 2001-2006 Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.trial import unittest
from twisted.spread import pb

class TestRemoteReferenceHash(unittest.TestCase):
    def test_hash(self):
        """test RemoteReference.__hash__ with RemoteReferences created
        by  Broker.remoteForName
        """
        
        broker = pb.Broker()
        ref = broker.remoteForName("root")
        hash(ref)

class TestBrokerCollect(unittest.TestCase):
    def test_gc_collect_broker(self):
        import weakref
        import gc
        
        broker = pb.Broker()
        ref = broker.remoteForName("root")
        broker.connectionLost("fake")
        
        called = []
        proxy=weakref.proxy(broker, lambda p: called.append(1))
        del broker
        gc.collect()
        self.failUnless(called, "broker alive and not garbage collected.")
