from twisted.internet.task import react, deferLater
from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import TCP4ClientEndpoint


class Greeter(Protocol):
    def dataReceived(self, data):
        print("Got:", repr(data))


async def txmain(reactor):
    point = TCP4ClientEndpoint(reactor, "localhost", 8080)
    protocol = await point.connect(Factory.forProtocol(Greeter))
    protocol.transport.setTcpNoDelay(True)
    protocol.transport.write(b"POST /_minerva/io/ HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n")
    while True:
        await deferLater(reactor, 0.01)
        print(".")
        protocol.transport.write(b"7" * 4096)


react(txmain, ())
