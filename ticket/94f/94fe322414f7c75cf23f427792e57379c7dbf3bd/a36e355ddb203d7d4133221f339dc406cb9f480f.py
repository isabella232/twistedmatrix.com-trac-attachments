#!/usr/bin/env python
import socket
from io import BytesIO
from time import sleep

from twisted.internet import reactor
from twisted.web.client import Agent, FileBodyProducer


def snoozer():
    # this is a slightly contrived example, but simulates the behaviour when
    # the process gets very busy, allowing us to reproduce the race condition
    # under test.
    sleep(1)
    print("tick")
    reactor.callLater(0, snoozer)


def test():
    # start a process which will make the reactor run slowly
    reactor.callLater(0, snoozer)

    # open a socket we can try connect to
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(('127.0.0.1', 0))
    serversocket.listen(5)
    (_, port) = serversocket.getsockname()

    # fire off a request
    print("starting request")
    agent = Agent(reactor)
    d = agent.request(
        b"POST", b"http://localhost:%i" % (port, ),
        bodyProducer=FileBodyProducer(BytesIO(b"test")),
    )

    # arrange for it to be cancelled after* connect completes, but before
    # any data is written to the socket.
    def cancel_it():
        print("cancelling request")
        d.cancel()
    reactor.callLater(1.5, cancel_it)

    # catch and log the failure of the request
    def log_err(f):
        print("Request failed: %s" % (f,))
        return None
    d.addErrback(log_err)

    # shut down the reactor when we're done
    def stop_reactor(result):
        serversocket.close()
        reactor.stop()
        return result
    d.addBoth(stop_reactor)


reactor.callWhenRunning(test)
reactor.run()
