from twisted.internet import protocol, reactor
from twisted.application import service, internet

class NotifyProtocol(protocol.Protocol):
    def __init__(self):
        self.host_key = None
    def dataReceived(self, data):
        self.factory.count += 1
        print "%s clients have connected." % self.factory.count
        self.transport.write("HTTP/1.x 200 OK\r\n\r\n")

class NotifyFactory(protocol.ServerFactory):
    protocol = NotifyProtocol
    def __init__(self):
        self.count = 0

application = service.Application('NotifyServer')
internet.TCPServer(2000, NotifyFactory(), interface="0.0.0.0", backlog=50000).setServiceParent(service.IServiceCollection(application))
