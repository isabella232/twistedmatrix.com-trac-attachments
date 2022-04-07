from __future__ import print_function
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 bg=dark

import re
import datetime

from twisted.web.client import ProxyAgent, readBody
from twisted.internet import reactor, defer, task
from twisted.internet.endpoints import TCP4ClientEndpoint, HostnameEndpoint
from twisted.internet.protocol import ProcessProtocol
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.internet.error import ProcessDone, ProcessTerminated
from twisted.python.failure import Failure
from twisted.internet import reactor
from twisted.logger import Logger

log = Logger('OVAL')

class ProcessException(Exception): pass
class OVALInvalid(Exception): pass

class ReadCURL(ProcessProtocol):
    def __init__(self, d):
        self._deferred = d
        #ProcessProtocol.__init__(self)

    def childConnectionLost(self, *args):
        print('Connection lost', *args)
        return ProcessProtocol.childConnectionLost(self, *args)

    def connectionMade(self):
        self.sout= []
        self.serr = []

    def outReceived(self, data):
        log.debug('outrec')
        self.sout.append(data)

    def errReceived(self, data):
        log.debug('errrec')
        self.serr.append(data)

    def processEnded(self, reason):
        log.debug('Process ended')
        log.debug(str(reason))

    def processExited(self, reason):
        print('Process exited')
        log.debug('Process exited')
        log.debug(str(reason))

        if reason.value.exitCode == 0:
            self._deferred.callback(b''.join(self.sout))
        else:
            self._deferred.errback(ProcessException('%s\nStderr: %s' %(str(reason.value), b''.join(self.serr).decode())))


class CurrentOVAL:
    def __init__(self, ovaldefinitions, proxyurl):
        self.ovaldefinitions = ovaldefinitions
        self.proxyurl = proxyurl
        self._data = None
        self._dataExpires = None

        self.contentLength = 0

        self._dataExpires = None
        self._dataDownload = None
        self.current_proc=None

        log.debug('init')

    def checkOutput(self, sout):
        log.debug('defer Fired')
        output = sout.decode()
        log.debug(output)

    def logFailure(self, failure):
        print(failure)
        log.debug('a failure')
        log.failure('boo', failure=failure)

    def download(self):
        log.debug('Checking if new file needed')
        d = defer.Deferred()
        proto = ReadCURL(d)
        cmd = ['/usr/bin/curl', '-x', self.proxyurl, '-I', self.ovaldefinitions]
        log.debug(str(cmd))
        self.current_proc = reactor.spawnProcess(proto, cmd[0], cmd)
        d.addCallback(self.checkOutput)
        d.addErrback(self.logFailure)
        return d
from twisted.application.service import Application
from twisted.application import internet, service
application = Application("POC")

c = CurrentOVAL(b'https://www.redhat.com/security/data/oval/com.redhat.rhsa-all.xml.bz2', 'http://proxy:8080')
c.download()
