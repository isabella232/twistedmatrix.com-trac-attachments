from __future__ import (unicode_literals, division,
                        print_function, absolute_import)

from cStringIO import StringIO
import logging

from twisted.internet import task, protocol
from twisted.web import client
from twisted.python import log
from twisted.protocols.basic import LineReceiver


class DropConnectionAfterEmptyLine(LineReceiver):
    MAX_LENGTH = 1000

    def lineReceived(self, line):
        print("Line received", line)

    def lineLengthExceeded(self, line):
        print("Length exceeded")
        self.transport.loseConnection()


class DropperFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return DropConnectionAfterEmptyLine()


def main(reactor, *args):
    observer = log.PythonLoggingObserver()
    observer.start()
    logging.basicConfig(level=logging.DEBUG)

    dropper = DropperFactory()

    reactor.listenTCP(27500, dropper)

    s = StringIO(b'X' * 265000)
    bodyProducer = client.FileBodyProducer(s, readSize=1024)
    ## This seems to fix the issue

    # class SmartFileBodyProducer(client.FileBodyProducer):
    #     """
    #     Subclass of `twisted.web.client.FileBodyProducer` that guards itself
    #     from being stopped multiple times.

    #     """

    #     def stopProducing(self):
    #         if not hasattr(self, "_task"):
    #             # Protect myself from being called second time
    #             return
    #         super(SmartFileBodyProducer, self).stopProducing()
    #         del self._task

    # bodyProducer = SmartFileBodyProducer(s, readSize=1024)

    agent = client.Agent(reactor)

    req = agent.request(
        b'POST', b'http://localhost:27500',
        headers=client.Headers({b'Content-Type': [b'application/json']}),
        bodyProducer=bodyProducer)

    def on_headers_received(x):
        print("Resp code", x.code)
        print("Resp headers:", x.headers, sep='\n')
        return client.readBody(x)

    def on_body_received(x):
        print("Resp body:", x, sep='\n')

    def req_errback(x):
        x.printTraceback()
        print("Req error:", x)
        pass

    req.addCallback(on_headers_received)
    req.addCallback(on_body_received)
    req.addErrback(req_errback)
    return req


if __name__ == '__main__':
    task.react(main)
