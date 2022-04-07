#!/usr/bin/env python
"""Serve as a sample implementation of a twisted producer/consumer
system, with a simple TCP server which asks the user how many random
integers they want, and it sends the result set back to the user, one
result per line, and then closes the connection.

Requires python 2.6 and twisted 8.2.0 or above."""

import random

from zope.interface import implements
from twisted.internet import interfaces, reactor
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver

class Producer:
    """Send back the requested number of random integers to the client."""
    implements(interfaces.IPushProducer)
    def __init__(self, proto, cnt):
        self._proto = proto
        self._goal = cnt
        self._produced = 0
        self._paused = False
    def pauseProducing(self):
        """When we've produced data too fast, pauseProducing() will be
called (reentrantly from within resumeProducing's transport.write
method, most likely), so set a flag that causes production to pause
temporarily."""
        self._paused = True
        print('pausing connection from %s' % (self._proto.transport.getPeer()))
    def resumeProducing(self):
        self._paused = False
        while not self._paused and self._produced < self._goal:
            next_int = random.randint(0, 10000)
            self._proto.transport.write('%d\r\n' % (next_int))
            self._produced += 1
        if self._produced == self._goal:
            self._proto.transport.unregisterProducer()
            self._proto.transport.loseConnection()
    def stopProducing(self):
        pass

class ServeRandom(LineReceiver):
    """Serve up random data."""
    def connectionMade(self):
        print('connection made from %s' % (self.transport.getPeer()))
        self.transport.write('how many random integers do you want?\r\n')
    def lineReceived(self, line):
        cnt = int(line.strip())
        producer = Producer(self, cnt)
        self.transport.registerProducer(producer, True)
        producer.resumeProducing()
    def connectionLost(self, reason):
        print('connection lost from %s' % (self.transport.getPeer()))
factory = Factory()
factory.protocol = ServeRandom
reactor.listenTCP(1234, factory)
print('listening on 1234...')
reactor.run()
