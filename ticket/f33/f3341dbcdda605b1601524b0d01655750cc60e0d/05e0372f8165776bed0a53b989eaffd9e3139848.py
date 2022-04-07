from twisted.spread import pb
from twisted.internet import reactor

class Data(pb.Cacheable, pb.RemoteCache, object):
    pass

pb.setUnjellyableForClass(Data, Data)
    
class testRoot(pb.Root):
    def remote_echo(self, dat):
	    print dat

def copydata(r):
    dat = Data()
    d = r.callRemote("echo", dat)
    d.addCallback(lambda x: reactor.stop())

if __name__ == '__main__':
    reactor.listenTCP(8789, pb.PBServerFactory(testRoot()))
    factory = pb.PBClientFactory()
    reactor.connectTCP("127.0.0.1", 8789, factory)
    factory.getRootObject().addCallback(copydata)
    reactor.run()

