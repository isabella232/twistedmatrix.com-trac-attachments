from twisted.internet import glib2reactor
glib2reactor.install()

import twisted.internet.utils
import twisted.internet.reactor

class Test:

	def __init__(self):
		twisted.internet.reactor.callWhenRunning(self.execute_test)
		twisted.internet.reactor.run()

	def execute_test(self):
		deferred = self.test()
		deferred.addCallback(self.print_)
	
	def print_(self, result):
		print result
	
	def test(self):
		deferred = twisted.internet.utils.getProcessOutput('/bin/echo', ['test'])
		return deferred

Test()
