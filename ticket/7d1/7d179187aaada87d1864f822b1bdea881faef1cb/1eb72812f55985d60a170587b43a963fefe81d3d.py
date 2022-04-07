from twisted.internet import task, protocol, endpoints, defer
from OpenSSL import SSL


class Echo(protocol.Protocol):
    def dataReceived(self, data):
        print(data)

    def connectionMade(self):
        self.transport.write("Hello, world!")


class NoVerifyContextFactory:
    isClient = 1

    method = SSL.SSLv23_METHOD

    _contextFactory = SSL.Context

    def getContext(self):
        ctx = self._contextFactory(self.method)
        ctx.set_options(SSL.OP_NO_SSLv2)
        ctx.set_options(SSL.VERIFY_NONE)
        return ctx


@defer.inlineCallbacks
def main(reactor):
    factory = protocol.Factory.forProtocol(Echo)
    endpoint = endpoints.SSL4ClientEndpoint(reactor, 'localhost', 8000,
                                            NoVerifyContextFactory())
    echoClient = yield endpoint.connect(factory)
    reactor.callLater(1, echoClient.transport.loseConnection)
    done = defer.Deferred()
    echoClient.connectionLost = lambda reason: done.callback(None)
    yield done

if __name__ == '__main__':
    task.react(main)
