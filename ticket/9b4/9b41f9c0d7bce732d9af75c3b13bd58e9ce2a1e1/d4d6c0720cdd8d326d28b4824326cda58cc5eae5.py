
import sys
from twisted.internet import protocol
from twisted.internet import reactor

class MyPP(protocol.ProcessProtocol):
    def __init__(self, verses):
        self.verses = verses
        self.data = ""
    def connectionMade(self):
        print "connectionMade!"
        self.transport.closeStdin() # tell them we're done
    def outReceived(self, data):
        self.data = self.data + data
    def errReceived(self, data):
        self.data = self.data + data
    def processEnded(self, status_object):
        print "processEnded, status %d" % status_object.value.exitCode
        print "quitting"
        print self.data
        reactor.stop()

def starter():
    pp = MyPP(10)
    reactor.spawnProcess(pp, sys.executable, [sys.executable, "openSocketChild.py"], {})

reactor.callLater(0, starter)

from twisted.application import service
application = service.Application('pydapserver')

