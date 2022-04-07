#!/usr/bin/env python

# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

from zope.interface import implementer

from twisted.cred import portal, checkers
from twisted.spread import pb
from twisted.internet import reactor


class ChatServer:
    def __init__(self):
        self.groups = {}  # indexed by name

    def joinGroup(self, groupname, user, allowMattress):
        if groupname not in self.groups:
            self.groups[groupname] = Group(groupname, allowMattress)
        self.groups[groupname].addUser(user)
        return self.groups[groupname]


@implementer(portal.IRealm)
class ChatRealm:
    def requestAvatar(self, avatarID, mind, *interfaces):
        assert pb.IPerspective in interfaces
        avatar = User(avatarID)
        avatar.server = self.server
        avatar.attached(mind)
        return pb.IPerspective, avatar, lambda a=avatar: a.detached(mind)


class User(pb.Avatar):
    def __init__(self, name):
        self.name = name
        self.groups = []

    def attached(self, mind):
        self.remote = mind

    def detached(self, mind):
        #for group in self.groups:
        #    n = group.users.index(self)
        #    del group.users[n]
        self.remote = None

    def perspective_joinGroup(self, groupname, allowMattress=True):
        group = self.server.joinGroup(groupname, self, allowMattress)
        self.groups.append(group)
        return group

    def send(self, message):
        if self.remote is not None:
            self.remote.callRemote("print", message)


class Group(pb.Viewable):
    def __init__(self, groupname, allowMattress):
        self.name = groupname
        self.allowMattress = allowMattress
        self.users = []

    def addUser(self, user):
        self.users.append(user)

    def view_send(self, from_user, message):
        if not self.allowMattress and "mattress" in message:
            raise ValueError("Don't say that word")
        for user in self.users:
            user.send("<{}> says: {}".format(from_user.name, message))


realm = ChatRealm()
realm.server = ChatServer()
checker = checkers.InMemoryUsernamePasswordDatabaseDontUse()
checker.addUser(b"alice", b"1234")
checker.addUser(b"bob", b"secret")
checker.addUser(b"carol", b"fido")
p = portal.Portal(realm, [checker])

reactor.listenTCP(8721, pb.PBServerFactory(p))
reactor.run()