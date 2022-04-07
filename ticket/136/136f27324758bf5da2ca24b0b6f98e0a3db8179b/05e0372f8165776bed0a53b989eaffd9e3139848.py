from OpenSSL import SSL
from twisted.internet import reactor, ssl
from twisted.internet.protocol import ClientFactory, ReconnectingClientFactory
from twisted.protocols.basic import LineReceiver


class ClientTLSContext(ssl.ClientContextFactory):
    isClient = 1
    def getContext(self):
        return SSL.Context(SSL.TLSv1_METHOD)


class TLSClient(LineReceiver):
    pretext = []

    posttext = [
        "HEAD / HTTP/1.1",
        "Host: www.google.com",
        "",
        ]

    def connectionMade(self):
        print("Connection made")
        ctx = ClientTLSContext()
        self.transport.startTLS(ctx, self.factory)

        # self.setTimeout(0.5)

        for l in self.posttext:
            print "send", repr(l)
            self.sendLine(l)

    def lineReceived(self, line):
        print("received: " + line)
        # self.resetTimeout()
        if line == '':
            r = raw_input('[S]top or [D]isconnect ').lower() 

            if r == 's':
                self.transport.abortConnection()
            else:
                self.transport.loseConnection()
                # self.transport.transport.loseConnection()
                # In our actual software, transport has a transport attribute too
                # calling self.transport.transport.loseConnection() will correctly
                # close and reconnect


class TLSClientFactory(ReconnectingClientFactory):
    protocol = TLSClient
    initialDelay = 0.1

    def clientConnectionFailed(self, connector, reason):
        print "connection failed: ", reason.getErrorMessage()
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print "connection lost: ", reason.getErrorMessage()
        if 'aborted' in reason.getErrorMessage():
            reactor.stop()
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

if __name__ == "__main__":
    factory = TLSClientFactory()
    reactor.connectTCP('localhost', 4443, factory)
    reactor.run()
