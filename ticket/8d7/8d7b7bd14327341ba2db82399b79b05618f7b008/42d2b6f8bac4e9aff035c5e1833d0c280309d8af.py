from twisted.internet import reactor, defer
from twisted.internet.task import LoopingCall
from twisted.python import log
from collections import deque
import sys

log.startLogging(sys.stdout)
defer.setDebugging(True)

data = deque([1,2,3])

LC = None

def results(result):
    LC.stop()
    LC.start(3)
    print result
    
def bar(x):
    d = defer.Deferred()
    reactor.callLater(2, d.callback, x * 3)
    return d

def foo():
    global LC      
    if data:
        getdata = data.popleft() 
        d = bar(getdata)
        d.addCallback(results)
        return d
    else:
        LC.close()
    return

LC = LoopingCall(foo)
LC.start(3)
reactor.run()