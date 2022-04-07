from twisted.internet import reactor, defer

def end(x):
    reactor.stop()
    # reactor._started = False
    print "Stopped reactor"

d = defer.Deferred()
reactor.callLater(1, d.callback, None)
d.addCallback(end)
reactor.run()
assert not reactor._started

d = defer.Deferred()
reactor.callLater(1, d.callback, None)
d.addCallback(end)
assert not reactor._started
reactor.run()
