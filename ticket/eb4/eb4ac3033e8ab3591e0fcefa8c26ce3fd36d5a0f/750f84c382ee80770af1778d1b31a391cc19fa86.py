
from twisted.internet.test.reactormixins import ReactorBuilder
from twisted.internet.gtk2reactor import Gtk2Reactor

class JustBuildIt(ReactorBuilder):

    def __init__(self):
        self.cleanups = []

    reactorFactory = Gtk2Reactor

    def getTimeout(self):
        return 1.0

    def flushLoggedErrors(self):
        return []

    def addCleanup(self, f, *a, **k):
        self.cleanups.append(lambda : f(*a, **k))

    def finish(self):
        for cleanup in self.cleanups:
            cleanup()

def once():
    oneBuilder = JustBuildIt()
    oneReactor = oneBuilder.buildReactor()
    def andstop():
        oneReactor.stop()
    oneReactor.callLater(0.1, andstop)
    oneBuilder.runReactor(oneReactor)
    oneBuilder.finish()

import os
once()
first = os.listdir("/dev/fd")
once()
second = os.listdir("/dev/fd")
once()
third = os.listdir("/dev/fd")

if len(first) != len(second) or len(first) != len(third):
    print "Leaked."
    print first
    print second
    print third
else:
    print "Did not leak."

