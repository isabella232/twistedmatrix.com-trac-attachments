#!/usr/bin/env python
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Print a simple bar chart of ping round trip times eg

 python pingbars.py www.example.com
"""

import os, re, sys

from twisted.internet.defer import Deferred
from twisted.internet.endpoints import connectProtocol, ProcessEndpoint
from twisted.internet.error import ConnectionDone, ConnectionLost
from twisted.protocols.basic import LineOnlyReceiver
from twisted.python import log, usage



class PingRttPrinter(LineOnlyReceiver):
    delimiter = '\n'
    pingLine = re.compile(
        r'^\d+ bytes from [^:]+: '
        r'icmp_seq=\d+ ttl=\d+ time=(?P<rtt>[\d.]+) ms$')

    _offset = None

    def __init__(self):
        self.finished = Deferred()
        self._consoleWidth = int(os.environ.get('COLUMNS', '80'))


    def connectionMade(self):
        self._pid = self.transport.pid
        log.msg(format='process started. pid: %(pid)s', pid=self._pid)


    def lineReceived(self, line):
        m = self.pingLine.match(line)
        if m:
            rtt = float(m.group('rtt'))
            if self._offset is None:
                self._offset = max(0, rtt - (self._consoleWidth / 2))

            label = ('%.1f' % (rtt,)).rjust(6)
            barWidth = int(rtt - self._offset)
            bar = '.' * min(max(0, barWidth), self._consoleWidth)

            if barWidth > self._consoleWidth:
                bar = bar[:-1] + '>'
            elif barWidth < 0:
                bar = '<' + bar[1:]

            sys.stdout.write(label + ' ' + bar + '\n')
            sys.stdout.flush()
        else:
            log.msg(format='unrecognised line: %(line)r', line=line)


    def connectionLost(self, reason):
        sys.stdout.write('\n')
        sys.stdout.flush()
        try:
            reason.trap(ConnectionDone, ConnectionLost)
        except:
            self.finished.errback()
        else:
            log.msg(
                format='process exited. pid: %(pid)s, reason: %(reason)r',
                pid=self._pid, reason=reason.value)
            self.finished.callback(reason.value)



def startPing(reactor, options):
    d = connectProtocol(
        ProcessEndpoint(
            reactor,
            '/usr/bin/ping',
            args=('/usr/bin/ping', '-n', options['host'])),
        PingRttPrinter())

    @d.addCallback
    def waitForProcess(proto):
        return proto.finished

    return d



class Options(usage.Options):
    synopsis = "%s [OPTIONS] HOST" % (os.path.basename(sys.argv[0]),)
    optFlags = [
        ["verbose", "v", "Enable verbose logging to stderr."],
    ]

    def parseArgs(self, host):
        self['host'] = host



def main(reactor):
    options = Options()

    try:
        options.parseOptions()
    except usage.UsageError as errortext:
        sys.stderr.write(str(options) + '\n')
        sys.stderr.write('ERROR: %s\n' % (errortext,))
        raise SystemExit(1)

    if options['verbose']:
        log.startLogging(sys.stderr)

    return startPing(reactor, options)



if __name__ == '__main__':
    from twisted.internet.task import react
    react(main)
