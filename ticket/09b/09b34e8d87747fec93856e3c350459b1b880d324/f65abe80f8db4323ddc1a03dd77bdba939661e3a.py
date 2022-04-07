from twisted.internet import reactor, defer

# a small, reproducable error in memory usage when using t.i.defer.DeferredList
# see raise_or_return

# a few more details:
# python -v = Python 2.4.4 (#1, Oct 18 2006, 10:34:39) 
#             [GCC 4.0.1 (Apple Computer, Inc. build 5341)] on darwin

# twisted version: >>> import twisted
#                  >>> twisted.version
#                  Version('twisted', 2, 5, 0)  # (SVN r19573)

def raise_or_return():
    # raising an exception causes the process
    # to use approx 70 MB of memory on my 10.4.6 OSX
    # when we're done (peaks at 270 MB memory used.)

    raise Exception('foobar')

    # however, returning this exception causes the process
    # to only use 7 MB of memory on the same machine.

    #return Exception('foobar')


def run():
    ds = []
    for i in xrange(2000):
        ds.append(defer.maybeDeferred(raise_or_return))
    dl = defer.DeferredList(ds, consumeErrors=True)
    dl.addCallback(lambda result: done())
    return dl

def stop():
    reactor.stop()
    print 'press any key to exit process.'
    raw_input()

def done():
    print 'done.'
    reactor.callLater(0.1, stop)

reactor.callLater(0, run)
reactor.run()
