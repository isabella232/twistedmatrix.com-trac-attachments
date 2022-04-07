from twisted.internet import protocol
from twisted.internet import reactor
import re

class MyPP(protocol.ProcessProtocol):
    def __init__(self, verses):
        pass
    def connectionMade(self):
        print "connectionMade!"
    def outReceived(self, data):
        print data
    def errReceived(self, data):
        print data
    def inConnectionLost(self):
        print "inConnectionLost"
    def outConnectionLost(self):
        print "outConnectionLost"
    def errConnectionLost(self):
        print "errConnectionLost"
    def processExited(self, reason):
        print "processExited"
    def processEnded(self, reason):
        print "processEnded"
        reactor.stop()

pp = MyPP(10)
reactor.spawnProcess(pp, "C:\\WINDOWS\\system32\\cmd.exe", ['C:\\WINDOWS\\system32\\cmd.exe', '/c', 'D:\\tmpvm4kro.bat'], {}, "D:\\")
reactor.run()