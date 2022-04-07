# Test getProcessOutput

import sys
from twisted.internet import reactor, utils

def stopme(x):
    reactor.stop()

d = utils.getProcessOutput(sys.argv[1], sys.argv[2:])
d.addCallback(sys.stdout.write)
d.addCallback(stopme)
reactor.run()
