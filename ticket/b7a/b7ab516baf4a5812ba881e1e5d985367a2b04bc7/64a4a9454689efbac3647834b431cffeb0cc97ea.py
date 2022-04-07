#!/usr/bin/env python
from twisted.internet import reactor, defer, task, ssl
from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import SSL4ClientEndpoint

from twisted.python.log import startLogging
from sys import stdout
startLogging(stdout)


junk = 'a'*1100 # simulate a small web response
ccf = ssl.ClientContextFactory()

class Echo(Protocol):
    def sendMessage(self):
        self.transport.write(junk)
        self.finished = defer.Deferred()
        return self.finished

    def dataReceived(self, data):
        self.transport.loseConnection()


    def connectionLost(self, reason):
        self.finished.callback(None)

class EchoFactory(Factory):
    noisy = False
    def buildProtocol(self, addr):
        return Echo()

def gotProtocol(p):
    p.sendMessage()

def error(err):
    print "Error:"
    print err

def do_work():
    while(1):
        # simulate making requests to 'different' hosts by always recreating endpoint
        point = SSL4ClientEndpoint(reactor, "localhost", 8000, ccf)
        d = point.connect(EchoFactory())
        d.addCallback(gotProtocol) # on connection
        d.addErrback(error)
        yield d

def stop(dummy):
    reactor.stop()

def main():
    max_runs = 5
    coop = task.Cooperator()
    work = do_work()
    deferreds = []
    for run in xrange(max_runs):
        d = coop.coiterate(work)
        deferreds.append(d)
    dl = defer.DeferredList(deferreds)
    dl.addCallback(stop)
    return dl


if __name__ == '__main__':
    main()
    reactor.run()
