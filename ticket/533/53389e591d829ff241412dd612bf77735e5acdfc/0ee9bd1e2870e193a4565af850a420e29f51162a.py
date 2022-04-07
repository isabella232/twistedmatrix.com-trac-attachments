#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2001-2009 Twisted Matrix Laboratories.
# See LICENSE for details.
import gobject
import pygtk
import gtk

# twisted imports
from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

# system imports
import time, sys

class MessageLogger:
    """
    An independent logger class (because separation of application
    and protocol logic is a good thing).
    """
    def __init__(self, file):
        self.file = file

    def log(self, message):
        """Write a message to the file."""
        timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
        self.file.write('%s %s\n' % (timestamp, message))
        self.file.flush()

    def close(self):
        self.file.close()


class LogBot(irc.IRCClient):
    """A logging IRC bot."""
    
    nickname = "twistedbot"
    
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.logger = MessageLogger(open(self.factory.filename, "a"))
        self.logger.log("[connected at %s]" % 
                        time.asctime(time.localtime(time.time())))

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.logger.log("[disconnected at %s]" % 
                        time.asctime(time.localtime(time.time())))
        self.logger.close()


    # callbacks for events

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        self.logger.log("[I have joined %s]" % channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        user = user.split('!', 1)[0]
        self.logger.log("<%s> %s" % (user, msg))
        
        # Check to see if they're sending me a private message
        if channel == self.nickname:
            msg = "It isn't nice to whisper!  Play nice with the group."
            self.msg(user, msg)
            return

        # Otherwise check to see if it is a message directed at me
        if msg.startswith(self.nickname + ":"):
            msg = "%s: I am a log bot" % user
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        self.logger.log("* %s %s" % (user, msg))

    # irc callbacks

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        self.logger.log("%s is now known as %s" % (old_nick, new_nick))


    # For fun, override the method that determines how a nickname is changed on
    # collisions. The default method appends an underscore.
    def alterCollidedNick(self, nickname):
        """
        Generate an altered version of a nickname that caused a collision in an
        effort to create an unused related name for subsequent registration.
        """
        return nickname + '^'



class LogBotFactory(protocol.ClientFactory):
    """A factory for LogBots.

    A new protocol instance will be created each time we connect to the server.
    """

    # the class of the protocol to build when new connection is made
    protocol = LogBot

    def __init__(self, channel, filename):
        self.channel = channel
        self.filename = filename

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()

class GUI(object):
    def __init__(self):
        self.mw = gtk.Window()
        self.mw.connect('destroy', self.quit)
        bt = gtk.Button('Run browser')
        bt.connect('clicked', self.on_click)
        frame = gtk.Frame('Click me')
        frame.add(bt)
        self.mw.add(frame)
        self.mw.show_all()
        f = LogBotFactory('#prova', 'botlog.txt')
        # connect factory to this host and port
        reactor.connectTCP(sys.argv[1], 6667, f)
        reactor.run()
  
    def on_click(self, b):
        url = 'http://www.gentoo.org'
        xdgProcess = XDGProcessProtocol()
        #####################################################
        # change the executable path of the browser you have
        #####################################################
        reactor.spawnProcess(xdgProcess, '/usr/bin/midori', ['/usr/bin/midori', url], None)    
        print 'clicked'
    
    def quit(self, w):
        print 'closeapp'
        try:
            reactor.stop()
        except:
            pass
        gtk.main_quit()
  
class XDGProcessProtocol(protocol.ProcessProtocol):
    def __init__(self):
        self.data = ''
    
    def connectionMade(self):
        pass
    
    def outReceived(self, data):
        self.data = self.data + data
    
    def errReceived(self, data):
        self.data = self.data + data
    def inConnectionLost(self):
        pass
    
    def outConnectionLost(self):
        print "outConnectionLost! The child closed their stdout!"
        print self.data
        
    def errConnectionLost(self):
        pass
    
    def processExited(self, reason):
        print "processExited, status %d" % (reason.value.exitCode,)
    
    def processEnded(self, reason):
        print "processEnded, status %d" % (reason.value.exitCode,)
        print "quitting"

if __name__ == '__main__':
    #########################################    
    # sys.argv[1] is the url of the irc server    
    #########################################
    # initialize logging
    log.startLogging(sys.stdout)
    
    GUI()
    gtk.main()
