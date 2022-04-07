from twisted.protocols.amp import Command, Integer, AMP


class Sum(Command):

    arguments = [("a", Integer()), ("b", Integer())]
    response = [("result", Integer())]


class Math(AMP):

    @Sum.responder
    def sum(self, a, b):
        return {"result": a + b}


class FakeTransport(object):

    def write(self, data):
        self.peer.dataReceived(data)

    def loseConnection(self):
        pass

    def getPeer(self):
        pass

    def getHost(self):
        pass


server = Math()
client = AMP()

server.makeConnection(FakeTransport())
client.makeConnection(FakeTransport())

server.transport.peer = client
client.transport.peer = server

result = []
client.callRemote(Sum, a=3, b=2).addCallback(result.append)

print result
