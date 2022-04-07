import base64
from hashlib import sha1

from twisted.internet import ssl, protocol, reactor


class FakeHTTP(protocol.Protocol):

    def connectionMade(self):
        print 'Connection made with', self.transport

    def dataReceived(self, data):
        print self.transport, "data received", data
        self.transport.write("HTTP/1.1 200 OK\r\nContent-length: 6\r\n\r\n")
        self.transport.write("Hello!")
        self.transport.loseConnection()

    def connectionLost(self, f):
        print self.transport, 'connection lost', f


if __name__ == '__main__':
    factory = protocol.Factory()
    factory.protocol = FakeHTTP
    reactor.listenSSL(10005, factory,
                      ssl.DefaultOpenSSLContextFactory(
            'ssl.key', 'ssl.pem'))
    reactor.run()
