# test-case-name: twisted.names.test.test_dns
# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tests for twisted.runner.procmon.
"""

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from twisted.trial import unittest
from twisted.runner import procmon
from twisted.internet import defer, reactor

def shouldStart(monitor, procname, delay = 0):
    d = defer.Deferred()
    def _(timeout):
        if procname in monitor.protocols:
            d.callback(True)
        elif timeout == 0:
            d.errback('Process %s not started within %i seconds'%(procname,delay))
        else:
            reactor.callLater(1, _, timeout-1)
    _(delay)
    return d

def shouldNotStart(monitor, procname, delay = 0):
    d = defer.Deferred()
    def _(timeout):
        if procname in monitor.protocols:
            d.errback('Process %s started before %i seconds'%(procname,delay))
        elif timeout == 0:
            d.callback(True)
        else:
            reactor.callLater(1, _, timeout-1)
    _(delay)
    return d

def shouldStop(monitor, procname, delay = 0):
    d = defer.Deferred()
    def _(timeout):
        if procname not in monitor.protocols:
            d.callback(True)
        elif timeout == 0:
            d.errback('Process %s not stopped within %i seconds'%(procname,delay))
        else:
            reactor.callLater(1, _, timeout-1)
    _(delay)
    return d

def shouldNotStop(monitor, procname, delay = 0):
    d = defer.Deferred()
    def _(timeout):
        if procname not in monitor.protocols:
            d.errback('Process %s not stopped within %i seconds'%(procname,delay))
        elif timeout == 0:
            d.callback(True)
        else:
            reactor.callLater(1, _, timeout-1)
    _(delay)
    return d


class ProcessMonitor(unittest.TestCase):
    """Encoding and then decoding various objects."""

    procargs = ['/bin/sh', '-c', 'sleep 2; echo hello']

    def testAddProcessWhenNotRunning(self):
        m = procmon.ProcessMonitor()
        m.addProcess('foo', self.procargs)
        d = shouldNotStart(m, 'foo', 5)
        return d
    
    def testAddProcessBeforeRunning(self):
        m = procmon.ProcessMonitor()
        m.addProcess('foo', self.procargs)
        m.startService()
        d = shouldStart(m, 'foo', 5)
        def _stop(*a):
            m.stopService()
            return shouldStop(m, 'foo', 5)
        d.addCallback(_stop)
        return d
    
    def testAddProcessWhenRunning(self):
        m = procmon.ProcessMonitor()
        m.startService()
        m.addProcess('foo', self.procargs)
        d = shouldStart(m, 'foo', 5)
        def _stop(*a):
            m.stopService()
            return shouldStop(m, 'foo', 5)
        d.addCallback(_stop)
        return d
