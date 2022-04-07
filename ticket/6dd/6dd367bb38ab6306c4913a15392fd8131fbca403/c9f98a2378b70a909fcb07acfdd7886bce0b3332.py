"""Try to reproduce a bug with Twisted
Manlio Perillo (manlio.perillo@gmail.com)

This small code causes 2 bugs and 1 strange behaviour.

Python 2.4.1 (#65, Mar 30 2005, 09:13:57) [MSC v.1310 32 bit (Intel)] on win32
Twisted 2.0.1


1. set doCrash = 0 and doStrange = 1
On my system I obtain:

exceptions.IOError: [Errno 12] Not enough space

well, this happens even without Twisted...
it seems to be a Windows problem

2. set doCrash = 0 and doStrange = 0
Now there is no exception...

But when I hit Ctrl-C to stop program execution I obtain:
Traceback (most recent call last):
          File bigwrite-twisted.py, line 54, in ?
            reactor.run()
          File twisted\internet\posixbase.py, line 200, in run
            self.mainLoop()
          File twisted\internet\posixbase.py, line 208, in mainLoop
            self.runUntilCurrent()
        --- <exception caught here> ---
          File twisted\internet\base.py, line 533, in runUntilCurrent
            call.func(*call.args, **call.kw)
          File twisted\internet\base.py, line 389, in _continueSystemEvent
            for callList in sysEvtTriggers[1], sysEvtTriggers[2]:
        exceptions.TypeError: unsubscriptable object

3. set doCrash = 1 and doStrange = 0
Now Python crashes when trying to print the data...
"""

import sys

from twisted.internet import reactor
from twisted.python import log


doCrash = 1
doStrange = 0

if doCrash:
    N = 10000
else:
    N = 100

def doBug():
    data = 'bla bla' * N

    if not doCrash:
        data = '\n'.join([data] * N)
    
    d = {
        1: [['DATA', ['XXX', 'YYY'], [data]]],
        2: [['DATA', ['ZZZ', 'WWW'], [data]]]
        }

    print "data:", data
    print "written"

    reactor.stop()


if not doStrange:
    log.startLogging(sys.stdout)

reactor.callLater(2, doBug)
reactor.run()
