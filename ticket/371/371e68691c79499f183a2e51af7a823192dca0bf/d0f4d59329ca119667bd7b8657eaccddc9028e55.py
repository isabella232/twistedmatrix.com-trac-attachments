from twisted.internet import epollreactor
epollreactor.install()

from multiprocessing import Process
import os
import socket
from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from twisted.web.http import HTTPClient

from twisted.python.log import startLogging
from twisted.python import log
import sys

startLogging(sys.stdout)
__author__ = 'nacim'

class WorkerConnection():
    def __init__(self, usocket):
        self.sock = usocket

    def doRead(self):
        log.msg("[{0}] DOREAD".format(os.getpid()))
        data = self.sock.recv(1024)

    #TODO: fix doWrite error ?!
    def doWrite(self):
        log.msg("[{0}] XXX this should not be called !! XXX".format(os.getpid()))


    def fileno(self):
        return self.sock.fileno()

    def connectionLost(self, reason):
        self.sock.close()

    def logPrefix(self):
        return "WORKER-{0}: ".format(os.getpid())


class WorkerProcessAndConnect(Process):
    def __init__(self, pipe):
        super(WorkerProcessAndConnect, self).__init__()
        self.pipe = pipe

    def run(self):
        log.msg("[{0}] Start Process Worker".format(os.getpid()))
        recvmsg_receiver = WorkerConnection(self.pipe)
        reactor.addReader(recvmsg_receiver)

        # now make a connection just to have an new FD registred for write event.
        def printp(p):
            log.msg('[{0}] create proto (fd={1})'.format(os.getpid(), p.transport.fileno()))

        d = ClientCreator(reactor, HTTPClient).connectTCP("www.google.fr", 443)
        d.addCallback(printp)

        reactor.run()

class WorkerProcess(Process):
    def __init__(self, pipe):
        super(WorkerProcess, self).__init__()
        self.pipe = pipe

    def run(self):
        log.msg("[{0}] Start Process Worker".format(os.getpid()))
        recvmsg_receiver = WorkerConnection(self.pipe)
        reactor.addReader(recvmsg_receiver)

        reactor.run()

p1, s1 = socket.socketpair()
w1 = WorkerProcessAndConnect(s1)
w1.start()

p2, s2 = socket.socketpair()
w2 = WorkerProcess(s2)
w2.start()

reactor.run()







