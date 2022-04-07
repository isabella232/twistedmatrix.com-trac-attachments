#!/usr/bin/env python
from twisted.internet import epollreactor
epollreactor.install()

from twisted.internet import reactor, defer, task, ssl
from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import SSL4ClientEndpoint

junk = 'a'*1100 # simulate a small web response
ccf = ssl.ClientContextFactory()

class Echo(Protocol):
    def sendMessage(self):
        print "Sending Junk"
        self.transport.write(junk)

    def dataReceived(self, data):
        print "Got Junk: %d"%len(data) # got it, drop it.
        self.transport.loseConnection()

class EchoFactory(Factory):
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
