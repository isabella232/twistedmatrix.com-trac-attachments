from twisted.internet import reactor, defer
import timeit

def benchQueue(number):
    queue = defer.DeferredQueue()
    gotten = []
    
    for i in xrange(number):
        queue.put(i)
        
    for i in xrange(number):
        queue.get().addCallback(gotten.append)
        
def bencher():
    t = timeit.Timer('for t in [10,100,1000]: benchQueue(t)', 'from __main__ import benchQueue')
    print t.timeit(100)
    reactor.stop()

reactor.callLater(1, bencher)
reactor.run()