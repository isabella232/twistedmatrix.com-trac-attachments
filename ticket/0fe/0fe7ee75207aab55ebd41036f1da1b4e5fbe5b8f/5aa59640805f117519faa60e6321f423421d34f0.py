#!/usr/bin/env python
# -*- coding: UTF8 -*-

from twisted.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

import sys

class LogBot(irc.IRCClient):
    """A logging IRC bot."""
    nickname = "ploper"

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
    
    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
	quitmsg = 'Connexion lost.'

# callbacks
    def signedOn(self):
        """Appeler quand le bot est connecte au server."""
        self.join(self.factory.channel)

    def action(self, user, channel, data):
        """This will get called when the bot sees someone do an action."""
	print "raw data from action : ",data
    
    def privmsg(self, user, channel, data):
        """Message sur le canal."""
	print "raw data from privmsg : ",data

class LogBotFactory(protocol.ClientFactory):
    """
    A factory for LogBots.
    A new protocol instance will be created each time we connect to the server.
    """
    # the class of the protocol to build when new connection is made
    protocol = LogBot
    def __init__(self, channel):
        self.channel = channel

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()
    
if __name__ == '__main__':
    # initialize logging
    log.startLogging(sys.stdout)
    # create factory protocol and application
    BOTconnection = LogBotFactory("glop")
    # connect factory to this host and port
    reactor.connectTCP("irc.freenode.net", 6667, BOTconnection)
    reactor.run() # run bot
