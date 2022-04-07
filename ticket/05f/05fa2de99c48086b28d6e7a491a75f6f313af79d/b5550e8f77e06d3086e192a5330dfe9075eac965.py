#!/usr/bin/env python

from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory
from twisted.web import http

port = 7000

class DumbHandler(http.HTTPChannel):
    def __del__(self):
        print 'del %x' % id(self)

    def __init__(self, *args):
        print 'Got connection in %x' % id(self)
        http.HTTPChannel.__init__(self, *args)

    def connectionLost(self, *args):
        print 'Lost connection in %x' % id(self)
        http.HTTPChannel.connectionLost(self, *args)
        del self.requests   # <-----  Fix

factory = ServerFactory()
factory.protocol = DumbHandler
reactor.listenTCP(port, factory)
reactor.run()
