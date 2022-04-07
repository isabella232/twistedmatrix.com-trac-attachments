#coding=utf-8
from twisted.internet import iocpreactor,protocol
iocpreactor.install()
from twisted.internet import reactor,defer,task

class EchoProtocol(protocol.Protocol):
    def dataReceived(self,data):
        self.transport.write(data)

class EchoFactory(protocol.Factory):
    dataLen = 0
    dataBuffer = ''
    def buildProtocol(self,addr):
        p = EchoProtocol()
        p.factory = self
        return p


if __name__ == "__main__":
    reactor.listenTCP(12345, EchoFactory())
    reactor.run()
