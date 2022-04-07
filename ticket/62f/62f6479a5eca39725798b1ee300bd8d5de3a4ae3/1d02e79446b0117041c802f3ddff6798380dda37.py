import sys

from twisted.internet import protocol
from twisted.internet import reactor

class PP(protocol.ProcessProtocol):
    def connectionMade(self):
        reactor.callLater(1, self.transport.write, 'x' * 4096)
        reactor.callLater(2, self.transport.write, 'x' * 4096)

    def processEnded(self, reason):
        reactor.stop()

subproc = """
from twisted.internet import protocol, stdio, reactor

class QQ(protocol.Protocol):
    def dataReceived(self, data):
        1/0

stdio.StandardIO(QQ())
reactor.run()
"""

def main():
    reactor.spawnProcess(
        PP(),
        sys.executable,
        ["python", "-c", subproc])
    reactor.run()

if __name__ == '__main__':
    main()
