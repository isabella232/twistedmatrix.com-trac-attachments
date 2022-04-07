import sys

from twisted.internet import defer, protocol, reactor

import memcache


def test(proto):
    l = []

    d = proto.set('foo', 'bar')
    l.append(d)

#     d = proto.set('egg', 8)
#     l.append(d)

#     wfd = proto.delete('foo')
#     l.append(d)

    wfd = proto.get('foo')
    l.append(d)

    return defer.DeferredList(l)
    

def callback(result):
    print result

def errback(reason):
    print reason.value


d = protocol.ClientCreator(reactor, memcache.MemCacheProtocol
                           ).connectTCP('localhost', 11211)
d.addCallback(test)
d.addCallback(callback).addErrback(errback).addBoth(lambda x: reactor.stop())
reactor.run()
