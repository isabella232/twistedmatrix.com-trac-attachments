#!/usr/bin/python2.3

from twisted.internet.defer import Deferred, DeferredList
from twisted.internet import reactor

def printResult(result):
    print result

deferred1 = Deferred()
deferred1.callback('one')

deferred2 = Deferred()

deferred3 = Deferred()
deferred3.callback('three')

dl = DeferredList([deferred1, deferred2, deferred3])

dl.addCallback(printResult)
dl.addCallback(lambda x: reactor.stop())

deferred2.callback('two')

reactor.run()

