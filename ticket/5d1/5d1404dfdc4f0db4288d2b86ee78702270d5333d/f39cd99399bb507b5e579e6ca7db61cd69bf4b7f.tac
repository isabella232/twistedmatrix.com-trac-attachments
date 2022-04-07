from time import time
from twisted.internet import protocol, reactor
from twisted.application import service, internet

class NotifyProtocol(protocol.Protocol):
    def dataReceived(self, data):
        now = time()
        change = now - self.factory.lastTime
        if change > self.factory.biggestDelay:
            print 'New slowest:', change
            self.factory.biggestDelay = change
        self.factory.lastTime = now
        self.factory.count += 1
        if self.factory.count % 1000 == 0:
            print "%s clients have connected." % self.factory.count
        self.transport.write("HTTP/1.x 200 OK\r\n\r\n")


class FirstNotifyProtocol(NotifyProtocol):
    def connectionMade(self):
        self.factory.lastTime = time()
        self.factory.protocol = NotifyProtocol
        NotifyProtocol.connectionMade(self)

class NotifyFactory(protocol.ServerFactory):
    protocol = FirstNotifyProtocol
    def __init__(self):
        self.count = 0
        self.lastTime = time()
        self.biggestDelay = 0

application = service.Application('NotifyServer')
internet.TCPServer(2000, NotifyFactory(), interface="0.0.0.0", backlog=50000).setServiceParent(service.IServiceCollection(application))
