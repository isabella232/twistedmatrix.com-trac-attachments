from twisted.spread import pb
from twisted.internet import reactor

class Echoer(pb.Root):
    def remote_echo(self, st):
        print 'echoing: %s ' % (st)
        self.st = st
        return st


if __name__ == '__main__':
    reactor.listenTCP(1234, pb.PBServerFactory(Echoer()))
    reactor.run()
                   
