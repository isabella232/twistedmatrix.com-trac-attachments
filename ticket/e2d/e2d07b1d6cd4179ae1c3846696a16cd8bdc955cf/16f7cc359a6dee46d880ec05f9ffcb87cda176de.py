# -*- coding: utf-8

import sys

from twisted.python import log
from twisted.internet import defer


# framework


def default_error_handler(debuginfo):
    log.msg("Unhandled error in Deferred:", isError=True)
    debugInfo = debuginfo._getDebugTracebacks()
    if debugInfo != '':
        log.msg("(debug: " + debugInfo + ")", isError=True)
    log.err(debuginfo.failResult)


class DebugInfo(defer.DebugInfo):
    _error_handler = None

    def __del__(self):
        if not self.failResult:
            return

        try:
            self._error_handler()
        except Exception, e:
            log.msg("Failed to catch unhandled error", isError=True)
            log.err(e)


def setErrorCollector(callable_):
    DebugInfo._error_handler = callable_


def restoreErrorCollector():
    callable_ = DebugInfo._error_handler
    DebugInfo._error_handler = default_error_handler
    return callable_


# Initial setup
restoreErrorCollector()


# User code


def custom_error_collector(debuginfo):
    from twisted.internet import reactor
    default_error_handler(debuginfo)
    reactor.stop()
    # …


def code_not_handling_error():
    try:
        assert False
    except Exception:
        print defer.fail()

def main():
    from twisted.internet import reactor

    log.startLogging(sys.stderr)
    # Guerilla patching, just for the sake of proof of concept.
    defer.DebugInfo = DebugInfo
    setErrorCollector(custom_error_collector)

    reactor.callLater(0.5, code_not_handling_error)
    reactor.run()


if __name__ == '__main__':
    main()
