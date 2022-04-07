from twisted.application.service import Application
from twisted.python.log import startLogging, msg, FileLogObserver, addObserver

application = Application("Broken logging")
# Watch what happens from a safe distance.
addObserver(FileLogObserver(file('failsafe.log', 'w')).emit)

startLogging(file('broken.log', 'w'))

msg("Hello, world!")
from twisted.internet import reactor
reactor.callLater(1, msg, "Tick!")
