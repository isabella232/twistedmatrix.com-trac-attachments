from twisted.internet import protocol, reactor, ssl

from OpenSSL import SSL


class CtxFactory(ssl.ClientContextFactory):

    def getContext(self):
        self.method = SSL.SSLv23_METHOD
        ctx = ssl.ClientContextFactory.getContext(self)
        ctx.use_certificate_file('/etc/passwd')
        ctx.use_privatekey_file('/etc/passwd')

        return ctx


class Protocol(protocol.Protocol):

    def connectionMade(self):
        print "connection made"

    def connectionLost(self, reason):
        print "connection lost", reason


class Factory(protocol.ClientFactory):

    protocol = Protocol


def timeout():
    print "TIMEOUT"
    reactor.stop()


reactor.connectSSL('twistedmatrix.com', 443, Factory(), CtxFactory())
reactor.callLater(3, timeout)
reactor.run()
