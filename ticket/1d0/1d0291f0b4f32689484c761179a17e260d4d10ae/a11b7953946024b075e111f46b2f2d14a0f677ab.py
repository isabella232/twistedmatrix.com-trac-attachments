import os
import os.path
import sys
import tempfile
import time

from twisted.internet import utils, reactor, defer, protocol
from twisted.python import log, util

def success(result):
    print "success"
    print result
    reactor.callLater(0, reactor.stop)

def failure(error):
    print "failure"
    print error
    reactor.callLater(0, reactor.stop)

def timeout():
    print "timeout"
    reactor.callLater(0, reactor.stop)

def search_path(exe):
    if '\\' in exe:
        return exe
    for path in os.environ['PATH'].split(os.pathsep):
        fullname = os.path.join(path, exe)
        if os.path.exists(fullname):
            return fullname
    raise Exception('not found')    
        
def work():
    d = utils.getProcessOutputAndValue(
        search_path('powershell.exe'),
        ('-Command', 'echo hello'),
        )
    d.addCallbacks(success, failure)
    reactor.callLater(10, timeout)

def main():
    log.startLogging(sys.stderr)
    reactor.callWhenRunning(work)
    reactor.run()

def monkeypatch():
    # Make the Twisted code close stdin when process is connected
    utils._EverythingGetter.connectionMade = lambda x: x.transport.closeStdin()

if __name__=='__main__':
    args = sys.argv[1:]
    if args and args[0]=='--fixed':
        monkeypatch()
    main()
