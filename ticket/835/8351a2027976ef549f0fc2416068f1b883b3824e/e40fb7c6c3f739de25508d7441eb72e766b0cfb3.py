#!/usr/bin/python
from twisted.internet import reactor, protocol, defer
from twisted.mail import imap4
from twisted.internet import ssl

USERNAME = 'fetchsimplifiedbodyerror@gmail.com'
PASSWORD = 'fetchsimplifiedbodyerrors'

SERVER = 'imap.gmail.com'
PORT = 993
contextFactory = ssl.ClientContextFactory()

def end(res, proto):
    print res
    return

def mailbox(res, proto):
    print "got mailbox", res
    d = proto.fetchSimplifiedBody("10:10", uid=True)
    d.addCallback(end, proto)
    d.addErrback(failed)
    return d

def loggedin(res, proto):
    print "logged in", res
    d = proto.examine("INBOX")
    d.addCallback(mailbox, proto)
    d.addErrback(failed)
    return d

def connected(proto):
    print "connected", proto
    d = proto.login(USERNAME, PASSWORD)
    d.addCallback(loggedin, proto)
    d.addErrback(failed)
    return d

def failed(f):
    print f
    return

def done(_):
    reactor.callLater(0, reactor.stop)

def main():
    c = protocol.ClientCreator(reactor, imap4.IMAP4Client)
    d = c.connectSSL(SERVER, PORT, contextFactory)
    d.addCallbacks(connected, failed)
    d.addBoth(done)

reactor.callLater(0, main)
reactor.run()
