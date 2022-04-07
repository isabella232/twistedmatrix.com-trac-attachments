from twisted.trial import unittest

from twisted.python import threadpool
from twisted.internet import reactor

class DummyBackend:
    def __init__(self):
	self.pool = threadpool.ThreadPool(10, 10)

	reactor.callWhenRunning(self._start)

    def _start(self):
	self.pool.start()
	reactor.addSystemEventTrigger('during', 'shutdown',
				      self._finalClose)
    
    def _finalClose(self):
	if self.pool:
	    self.pool.stop()

class HangTestCase(unittest.TestCase):
    def setUp(self):
	self.backend = DummyBackend()

	raise Exception, 'boom'

    def testHang(self):
	pass
