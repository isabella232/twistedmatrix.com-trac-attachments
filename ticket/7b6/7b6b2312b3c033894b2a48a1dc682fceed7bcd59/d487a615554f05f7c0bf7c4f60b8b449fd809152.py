from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.internet.address import IPv4Address, UNIXAddress
from twisted.internet.protocol import ClientFactory, ServerFactory

class MyServerProtocol(LineReceiver):
    def connectionMade(self):
        self.sendLine("Welcome")
    
    def lineReceived(self, line):
        print "SERVER RECEIVED: ", line, "VIA", self.transport.getHost()         

class MyClientProtocol(LineReceiver):
    def connectionMade(self):
        self.sendLine("Hello")
        
    def lineReceived(self, line):
        print "CLIENT RECEIVED: ", line, "VIA", self.transport.getHost() 
        
class MyServerFactory(ServerFactory):
    protocol = MyServerProtocol

class MyClientFactory(ClientFactory):
    protocol = MyClientProtocol

for addr in (UNIXAddress("/tmp/test.socket"), 
             IPv4Address("TCP", "127.0.0.1", 10080),):
    addr.listen(MyServerFactory())
    addr.connect(MyClientFactory())

reactor.callLater(0.1, reactor.stop)
reactor.run()
