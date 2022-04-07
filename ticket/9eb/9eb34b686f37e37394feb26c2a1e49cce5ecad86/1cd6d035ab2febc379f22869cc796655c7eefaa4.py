import sys

from twisted.internet import defer, protocol, reactor

import memcache


def test(proto):
    return proto.set('foo' * 500, 'bar')
    

def callback(result):
    print result

def errback(reason):
    print reason.value


d = protocol.ClientCreator(reactor, memcache.MemCacheProtocol
                           ).connectTCP('localhost', 11211)
d.addCallback(test)
d.addCallback(callback).addErrback(errback).addBoth(lambda x: reactor.stop())
reactor.run()
