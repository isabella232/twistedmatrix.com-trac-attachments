from sys import stdout

from twisted.python.log import startLogging
from twisted.internet.protocol import ServerFactory
from twisted.internet import reactor

import tempfile

startLogging(stdout)

reactor.listenUNIX(tempfile.mktemp(), ServerFactory())
reactor.listenTCP(0, ServerFactory())
reactor.run()
