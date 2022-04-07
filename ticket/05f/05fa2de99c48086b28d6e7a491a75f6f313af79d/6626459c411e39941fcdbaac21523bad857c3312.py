#!/usr/bin/env python

import sys

from twisted.internet import reactor
from twisted.web.client import getPage

class Crawl(object):
    def __init__(self, urls):
        self.urls = urls
        self.connections = 0
        self.count = 0
        reactor.callLater(0, self.run)

    def run(self):
        while self.connections < 100:
            self.count += 1
            u = self.urls.pop().strip()
            print "%6d GET" % self.count, u[:61]
            d = getPage(u) #, maxLength=10*1024*1024)
            d.addBoth(self.decConn)
            self.connections += 1
        reactor.callLater(0.1, self.run)

    def decConn(self, result):
        self.connections -= 1

c = Crawl(list(sys.stdin))
reactor.run()
