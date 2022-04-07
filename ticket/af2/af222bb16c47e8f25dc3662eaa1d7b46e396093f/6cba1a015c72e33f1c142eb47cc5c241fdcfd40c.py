from twisted.application import service
from twisted.runner.procmon import ProcessMonitor

application = service.Application("Test")
pm = ProcessMonitor()
pm.setServiceParent(application)

def main():
	pm.addProcess('echo', ['echo', 'test_message'])
	from twisted.internet import reactor
	reactor.callLater(3, pm.removeProcess, 'echo')

from twisted.internet import reactor
reactor.callWhenRunning(main)


