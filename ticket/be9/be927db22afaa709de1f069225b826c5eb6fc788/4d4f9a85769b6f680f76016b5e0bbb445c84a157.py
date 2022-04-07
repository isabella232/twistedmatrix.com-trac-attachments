
import sys
from twisted.python.log import startLogging, msg, addObserver
from twisted.python import failure
failure.traceupLength = 0

realstdout = sys.stdout
def showError(eventDict):
    if eventDict['isError']:
        realstdout.write(eventDict['failure'].getTraceback())
addObserver(showError)

startLogging(sys.stdout)
startLogging(sys.stdout)

msg("Hello, World!")
