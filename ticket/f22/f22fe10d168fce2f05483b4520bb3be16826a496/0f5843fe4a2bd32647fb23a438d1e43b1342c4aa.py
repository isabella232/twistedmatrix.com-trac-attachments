#! /usr/bin/python

from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor
import gtk

print "Resolver", reactor.resolver

class Foo:
    def __init__(self):
        self.w = gtk.Window()
        self.w.add(gtk.Label("Hello World"))
        self.w.show_all()
        reactor.callLater(3, self.start)
        reactor.callLater(5, self.failed)
    def start(self):
        d = reactor.resolve("www.twistedmatrix.com")
        d.addBoth(self.done)
    def done(self, res):
        print "done", res
        reactor.stop()
    def failed(self):
        print "timeout"
        reactor.stop()

f = Foo()
reactor.run()
