#coding=utf-8
from twisted.internet import iocpreactor
iocpreactor.install()
from twisted.internet import reactor,defer
from twisted.spread import pb
import time,cPickle


def main():
    @defer.inlineCallbacks
    def call():
        factory = pb.PBClientFactory()
        reactor.connectTCP("localhost",12345,factory)
        remoteD = yield factory.getRootObject()
        for i in range(5):
            begin = time.time()
            val = {"hello":"hello"*100,"foo":"bar","baz":100,u"these are bytes":(1,2,3)}
            defers2 = [remoteD.callRemote("bad", cPickle.dumps(val, 2)) for i in range(1000)]
            for d in defers2:
                yield d
            end = time.time()
            print end-begin
        reactor.stop()
    reactor.callLater(0,call)
    reactor.run()

if __name__ == "__main__":
    main()
