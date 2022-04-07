import sys, os
import md5

from twisted.internet import reactor, task

from twisted.web.client import getPage
from twisted.python.util import println

from itertools import count

cn = count()

def whatever():
    print cn.next()

def checkit(s):
    print md5.md5(s).hexdigest()

loop = task.LoopingCall(whatever)
loop.start(0.1)


d = getPage(sys.argv[1], checkit)
d.addCallback(checkit)
d.addErrback(lambda error:(println("an error occurred",error),reactor.stop()))
d.addCallback(lambda _: reactor.stop())

reactor.run()
