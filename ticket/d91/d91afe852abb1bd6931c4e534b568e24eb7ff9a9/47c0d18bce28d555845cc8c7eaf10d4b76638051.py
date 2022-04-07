#!/usr/bin/python

import os, signal, time
from twisted.internet import reactor, defer

def terminate():
    print "terminating ..."
    d = defer.Deferred()
    # do things that lasts long (eg. database, network, etc.)
    reactor.callLater(1, d.callback, None)
    return d

pid = os.getpid()
if os.fork():
    # parent
    reactor.addSystemEventTrigger('before', 'shutdown', terminate)
    reactor.run()
else:
    time.sleep(0.5)
    os.kill(pid, signal.SIGTERM)
    time.sleep(0.5)
    os.kill(pid, signal.SIGTERM)


# Output without patch:
# 1. 'terminate' method is called twice
"""
terminating...
terminating...
"""

# Output with patch:
# 1. 'terminate' method is called once, as expected
"""
terminating...
"""

