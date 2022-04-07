from twisted.trial import unittest
from twisted.internet import reactor, defer

class RemoveTriggerTestCase(unittest.TestCase):

    def setUp(self):
	def _setupDone(d):
	    return d.callback(None)

	self.start_ids = {}
	self.startups = {}

	for i in range(5):
	    name = 'startup%d' % (i,)
	    self.start_ids[name] = reactor.callWhenRunning(self._startup, name)
	    self.startups[name] = False

	d = defer.Deferred()
	reactor.callLater(5.0, _setupDone, d)
	return d

    def _startup(self, name):
	reactor.removeSystemEventTrigger(self.start_ids[name])
	self.startups[name] = True

    def testAllObjectsShutdown(self):
	self.failUnless(all(self.startups.values()),
			"Not all startup methods called.")
