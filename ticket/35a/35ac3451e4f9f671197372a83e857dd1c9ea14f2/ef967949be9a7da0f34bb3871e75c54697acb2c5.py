import sys

from twisted.logger import (
    Logger, globalLogBeginner, jsonFileLogObserver, textFileLogObserver
)
from twisted.internet import task, defer


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

    finished = defer.Deferred(None)
    @finished.addCallback
    def logPreQuit(ign):
        log.info('End state reached')
        return ign

    reactor.callLater(5.0, finished.callback, None)
    return finished

if __name__ == '__main__':
    start_logging()
    log.info(u'Starting main')
    task.react(main)
