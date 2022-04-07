import logging

from twisted.internet import reactor, defer
from twisted.internet.defer import Deferred
from twisted.logger import Logger
from twisted.logger import STDLibLogObserver, globalLogPublisher
from twisted.protocols.basic import LineReceiver
from twisted.web.client import Agent

log = Logger()


class MyProtocol(LineReceiver):

    def __init__(self, finished):
        self.finished = finished
        self.line_num = 0

    def lineReceived(self, line):
        log.info('lineReceived: {line}', line=line)
        self.line_num += 1
        if self.line_num == 5:
            raise ValueError('got 5 lines')

    def connectionLost(self, reason=None):
        log.info('connectionLost: {reason}', reason=reason)
        self.finished.callback(reason)


def cbProtocolError(reason=None):
    log.info('cbProtocolError: {reason}', reason=reason)
    reactor.stop()


def cbRequest(response):
    finished = Deferred()
    finished.addErrback(cbProtocolError)
    response.deliverBody(MyProtocol(finished))
    return finished


def do_request():
    agent = Agent(reactor)
    d = agent.request('GET', 'http://localhost:8000/')
    d.addCallback(cbRequest)


def main():
    logging.basicConfig(level=logging.DEBUG)
    defer.setDebugging(True)
    globalLogPublisher.addObserver(STDLibLogObserver())
    do_request()
    reactor.run()


if __name__ == '__main__':
    main()
