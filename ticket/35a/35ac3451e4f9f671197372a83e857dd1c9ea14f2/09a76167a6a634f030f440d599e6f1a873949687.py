import sys

from twisted.logger import (
    Logger, globalLogBeginner, jsonFileLogObserver, textFileLogObserver
)
from twisted.internet import defer


log = Logger()


def start_logging():
    observers = [
        jsonFileLogObserver(sys.stderr),
        #textFileLogObserver(sys.stderr),
    ]
    globalLogBeginner.beginLoggingTo(observers)


def failHard(ign):
    raise Exception('break stuff now')



def main(reactor):
    d = defer.Deferred(None)

    @d.addCallback
    def logPreFail(ign):
        log.info(u'About to call failHard')
        return ign

    d.addCallback(failHard)
    reactor.callLater(2.0, d.callback, None)
    reactor.callLater(4.0, reactor.stop)


if __name__ == '__main__':
    defer.setDebugging(True)
    start_logging()
    log.info(u'Starting main')
    from twisted.internet import reactor
    main(reactor)
    reactor.run()
