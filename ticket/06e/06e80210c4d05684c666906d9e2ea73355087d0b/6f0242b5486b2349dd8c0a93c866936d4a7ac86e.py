#!/usr/bin/env python

import tempfile

from zope.interface import implementer
from twisted.spread import pb
from twisted.cred import credentials, checkers, portal
from twisted.internet import reactor
from twisted.test.proto_helpers import StringTransport

class Client(pb.Referenceable):
    pass

def loggedIn(perspective):
    return perspective.callRemote('serverMethod')

class MyAvatar(pb.Avatar):
    def attached(self, mind):
        self.mind = mind
    def perspective_serverMethod(self):
        return self.mind.callRemote('clientMethod').addErrback(self.failed)
    def failed(self, f):
        raise f

@implementer(portal.IRealm)
class MyRealm(object):
    def requestAvatar(self, avatarId, mind, *interfaces):
        avatar = MyAvatar()
        avatar.attached(mind)
        return pb.IPerspective, avatar, lambda: None

portal = portal.Portal(MyRealm(), [checkers.AllowAnonymousAccess()])
serverFactory = pb.PBServerFactory(portal)
clientFactory = pb.PBClientFactory()

if False:
    transport = StringTransport()
    serverProtocol = serverFactory.buildProtocol(None)
    serverProtocol.makeConnection(transport)
    clientProtocol = clientFactory.buildProtocol(None)
    clientProtocol.makeConnection(transport)
else:
    socket = tempfile.mktemp()
    unixPort = reactor.listenUNIX(socket, serverFactory)
    reactor.connectUNIX(socket, clientFactory)

clientFactory.login(credentials.Anonymous(), client=Client()).addCallback(loggedIn)

reactor.run()
