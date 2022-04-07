from twisted.spread import pb
from twisted.internet import reactor

class Adder(pb.Referenceable):
    def __init__(self, a):
        self.a = a
        
    def add(self, b):
        return self.a + b

def step1(rootObj):
    d = rootObj.callRemote('echo', Adder(3))
    d.addCallback(step2)

def step2(adder):
    print 'received: %s' % (adder)
    print adder.add(6)
    reactor.stop()
    
factory = pb.PBClientFactory()
reactor.connectTCP("localhost", 1234, factory)
d = factory.getRootObject()
d.addCallback(step1)

reactor.run()
