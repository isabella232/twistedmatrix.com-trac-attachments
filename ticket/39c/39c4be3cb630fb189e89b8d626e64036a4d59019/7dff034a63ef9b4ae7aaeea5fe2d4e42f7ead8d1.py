from ampoule import child, util
from twisted.protocols import amp

class Test(amp.Command):
    response = [("blocks", amp.String())]

class MyChild(child.AMPChild):
    @Test.responder
    def test(self):
        return {"blocks": '\x00'*4073}

@util.mainpoint
def main(args):
    import sys
    from twisted.internet import reactor, defer
    from twisted.python import log

    from ampoule import pool
    
    @defer.inlineCallbacks
    def _run():
        pp = pool.ProcessPool(MyChild, min=1, max=1)
        yield pp.start()
        result = yield pp.doWork(Test)
        print "You will not see this."
        yield pp.stop()
        reactor.stop()
    
    reactor.callLater(1, _run)
    reactor.run()
