from twisted.internet import reactor, defer, task

count = 0

def loopMe():
    print 'loop'
    global count
    count += 1

    d = defer.Deferred()

    if count < 3:
        reactor.callLater(.33, c.stop)
    if count < 2:
        reactor.callLater(.66, c.start, 0)

    reactor.callLater(1, d.callback, None)
    return d



class LC(task.LoopingCall):
    def start(self, *a, **kw):
        print 'starting'
        task.LoopingCall.start(self, *a, **kw)

    def stop(self, *a, **kw):
        print 'stoping'
        task.LoopingCall.stop(self, *a, **kw)

    def __call__(self):
        def cb(result):
            print 'cb'
            if self.running:
                self._reschedule()
            else:
                d, self.deferred = self.deferred, None
                d.callback(self)

        def eb(failure):
            print 'eb'
            try:
                self.running = False
                d, self.deferred = self.deferred, None
                d.errback(failure)
            except:
                print self.f
                failure.printTraceback()
                raise

        self.call = None
        d = defer.maybeDeferred(self.f, *self.a, **self.kw)
        d.addCallback(cb)
        d.addErrback(eb)

c = LC(loopMe)
c.start(0)
reactor.run()
