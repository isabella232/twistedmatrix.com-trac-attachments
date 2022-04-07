import sys
import threading
from twisted.internet.protocol import Protocol, Factory
if sys.platform == 'win32':
    from twisted.internet import iocpreactor
    iocpreactor.install()
from twisted.internet import reactor
from zope.interface import implements
from twisted.internet.interfaces import IHalfCloseableProtocol

class Echo(Protocol):
    implements(IHalfCloseableProtocol)
    def dataReceived(self, data):
        self.transport.write(data)
    def readConnectionLost(self):
        self.transport.loseWriteConnection()
    def writeConnectionLost(self):
        self.transport.loseConnection()

class Server(threading.Thread):
    def __init__(self, port):
        self.port = port
    def run(self):
        f = Factory()
        f.protocol = Echo
        reactor.listenTCP(self.port, f)
        reactor.run()
    def stop(self):
        reactor.stop()

if __name__ == '__main__':
    Server(7).run()
