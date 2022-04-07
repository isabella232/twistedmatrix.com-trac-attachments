from twisted.internet import reactor
from twisted.internet.defer import Deferred, DeferredList
from twisted.internet.task import Cooperator

MAX_SIMULTANEOUS_CONNECTIONS = 10

def connectToServer(host, portNumber):
    d = Deferred()
    reactor.callLater(1, d.callback, "SUCCESS")
    return d

def makeLotsOfParallelConnections(host, portRange, connectionResultCallback):
    def connectionGenerator():
        for port in portRange:
            d = connectToServer(host, port)
            d.addCallback(connectionResultCallback, host, port)
            yield d
    work = connectionGenerator()
    coop = Cooperator()
    dl = DeferredList([coop.coiterate(work) for i in
                        xrange(MAX_SIMULTANEOUS_CONNECTIONS)])

    return dl

if __name__ == "__main__":
    import sys
    def printToStdout(res, host, port):
        sys.stdout.write("%s:%s %s\n" % (host, port, res))

    d = makeLotsOfParallelConnections("localhost", xrange(1,30), printToStdout)
    d.addCallback(lambda ign: reactor.stop())
    reactor.run()

