#!/usr/bin/env python
# -*- mode: python; tab-width: 4; indent-tabs-mode: nil; py-indent-offset: 4; -*-
# vim:et:sw=4:ts=4

import time
from twisted.web import server, xmlrpc
from twisted.internet import reactor
from twisted.python import log
import os
import sys
import commons

class S( xmlrpc.XMLRPC ):
    def xmlrpc_foo( self, x ):
        log.msg('server got: %s' % x)
        return 0

port = 8765
log.startLogging(sys.stdout)
pid = os.fork()
if pid: # parent = server
    reactor.listenTCP( port, server.Site( S() ) )
    reactor.run()
else: # child = client
    time.sleep(1.5)
    p = xmlrpc.Proxy( unicode('http://localhost:%d/' % port) )
    d = p.callRemote( 'foo', 'abc' )
    def done(result):
        log.msg( 'client done')
        reactor.stop()
    d.addCallback(done)
    d.addErrback(log.err)
    reactor.run()
