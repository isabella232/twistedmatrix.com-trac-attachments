# -*- mode: python -*-

import os

from twisted.application import service
from twisted.internet import protocol, reactor
from twisted.python import log

application = service.Application( "screen+spawnProcess test" )

class myProtocol( protocol.ProcessProtocol ):

    def outReceived( self, data ):
        log.msg( 'stdout: %s' % repr( data ) )

    def errReceived( self, data ):
        log.msg( 'stderr: %s' % repr( data ) )

    def processEnded( self, reason ):
        log.msg( 'processEnded: %s' % repr( reason ) )

class processRunner( service.Service ):
    def __init__( self ):
        self.setName( 'processRunner' )

    def startService( self ):
        service.Service.startService( self )
        proto = myProtocol()

        env = os.environ
        env['TERM'] = 'vt100'
        # can't get '-D -m' to work:
        # '-d -m' successfully creates a detached session and forks it out
        # '-D -m' should do the same but *not* fork, instead it ends right away and produces a 'Dead' screen in screen -list
        reactor.callWhenRunning( reactor.spawnProcess, proto, '/usr/bin/screen', args = [ '/usr/bin/screen', '-D', '-m', '-S', 'test', '-s', '/bin/bash' ], usePTY = True, env = env )

processRunner = processRunner()
processRunner.setServiceParent( application )
