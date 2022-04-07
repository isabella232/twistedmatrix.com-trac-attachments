import time
from twisted.internet.protocol import ClientCreator, BaseProtocol
from twisted.internet import defer

DATA = "*"

class SyncProtocol(BaseProtocol):

    def __init__(self, number):
        self.deferred = defer.Deferred()
        self.total = number
        self.number = 0

    def check(self):
        return self.deferred

    def dataReceived(self, data):
        for octet in data:
            if data != DATA:
                self.sessionError(Exception("Non-prompt character"))
                break
            else:
                self.number += 1

            if self.number >= self.total:
                self.sessionComplete()
                break

            self.transport.write(DATA)

    def connectionMade(self):
        print "Connection made!"
        self.start = time.time()
        self.transport.write(DATA)

    def sessionComplete(self):
        self.finishSession()
        self.deferred.callback(self.end - self.start)

    def sessionError(self, err):
        self.finishSession()
        self.deferred.errback(err)

    def finishSession(self):
        self.end = time.time()
        self.transport.loseConnection()

    def connectionLost(self, reason):
        pass


def print_error(failure):
    print failure.getErrorMessage()
    return failure

def print_time(duration):
    print "Time: %f" % duration

def go(reac):
    print "Using reactor: %s" % type(reac).__name__
    prc = ClientCreator(reactor, SyncProtocol, 500)
    d = prc.connectTCP("localhost", 31415)
    d.addCallback(lambda prot: prot.check())
    d.addCallback(print_time)
    d.addErrback(print_error)
    d.addBoth(lambda _: reac.stop())
    return d

if __name__ == "__main__":
    # from twisted.internet import gtk2reactor
    # gtk2reactor.install()
    from twisted.internet import reactor
    reactor.callWhenRunning(go, reactor)
    reactor.run()
