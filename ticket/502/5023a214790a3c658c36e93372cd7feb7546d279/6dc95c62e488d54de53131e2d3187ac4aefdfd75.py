from twisted.internet import reactor, defer

def printResult(result):
    print result

def code_from_site():
   deferred1 = defer.Deferred()
   deferred2 = defer.Deferred()
   deferred3 = defer.Deferred()
   dl = defer.DeferredList([deferred1, deferred2, deferred3])
   dl.addCallback(printResult)
   deferred1.callback('one')
   deferred2.errback('bang!')
   deferred3.callback('three')
   
reactor.callWhenRunning(code_from_site)

reactor.callLater(2.0, reactor.stop)

reactor.run()
