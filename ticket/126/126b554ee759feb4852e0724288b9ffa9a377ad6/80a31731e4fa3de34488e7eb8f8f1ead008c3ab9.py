#!/usr/bin/env python
import os
import struct
import sys
from twisted.cred.checkers import InMemoryUsernamePasswordDatabaseDontUse
from twisted.conch.avatar import ConchUser
from twisted.conch.ssh import common
from twisted.conch.ssh.session import SSHSession, ISession, SSHSessionProcessProtocol
from twisted.conch.ssh.factory import SSHFactory
from twisted.conch.ssh.keys import Key
from twisted.cred.portal import IRealm, Portal
from twisted.internet import reactor
from twisted.python import components, log
from zope import interface
log.startLogging(sys.stderr)


class TraceSession(SSHSession):
    def __init__(self, *args, **kw):
        SSHSession.__init__(self, *args, **kw)

    def request_exec(self, data):
        if not self.session:
            self.session = ISession(self.avatar)
        f,data = common.getNS(data)
        log.msg('executing command "%s"' % f)
        try:
            #pp = SSHSessionProcessProtocol(self)
            pp = TraceProcessProtocol(self)
            self.session.execCommand(pp, f)
        except:
            log.deferr()
            return 0
        else:
            self.client = pp
            return 1

class TraceProcessProtocol(SSHSessionProcessProtocol):
    def __init__(self, session):
        self.session = session

    def outReceived(self, data):
        log.msg('TPP.outReceived(...) %d bytes' % len(data))
        SSHSessionProcessProtocol.outReceived(self, data)

    def inConnectionLost(self):
        log.msg('TPP.inConnectionLost()')
        SSHSessionProcessProtocol.inConnectionLost(self)


class GitConchUser(ConchUser):
    def __init__(self, username):
        ConchUser.__init__(self)
        self.username = username
        #self.channelLookup.update({"session": SSHSession})
        self.channelLookup.update({"session": TraceSession})

        # Find git-shell path.
        # Adapted from http://bugs.python.org/file15381/shutil_which.patch
        path = os.environ.get("PATH", os.defpath)
        for dir in path.split(os.pathsep):
            full_path = os.path.join(dir, 'git-shell')
            if (os.path.exists(full_path) and 
                    os.access(full_path, (os.F_OK | os.X_OK))):
                self.shell = full_path
                break

    def logout(self): pass


class SimpleGitSession(object):
    interface.implements(ISession)

    def __init__(self, user):
        self.user = user

    def execCommand(self, proto, cmd):
        command = (self.user.shell, '-c', cmd)
        reactor.spawnProcess(proto, self.user.shell, command)

    def eofReceived(self): pass

    def closed(self): pass


class GitRealm(object):
    interface.implements(IRealm)

    def requestAvatar(self, username, mind, *interfaces):
        user = GitConchUser(username)
        return interfaces[0], user, user.logout




TEST_PRIV_KEY = '''-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEA1ZIkA7Z735yOLh0Es+gUPjwBa0BBx++lf/PwbNisl+YUc9sm
ve0oGJRUnS9v3EQLEoffDklH7DS2bIZm9K17LEGllLKF6D9i/WR4/7ruS2oZl54c
SuwnbzAPLxxFJuJW7dF6nUo0iAjD/su2jPL3WGpvRHxOnDA6QVag0lbqzznZMdtg
qUSmM3ErNEN0S+IydFXuoZYgdKte0qEoD6stk9d4HPJpvlc5Dfw2kA07SQ4lnlEp
HPoPSsRxAvkdDpEnG8QB1Q2J1etxB6xlOVe/K1e6j+08pBpqeC1mwPHGgCneIdwA
Sh+J1e1rMkLYZs0ZdJGuxQHlyYBqYetDTmw/NQIBIwKCAQBnvALdO2C9EYbjMqqD
RNah4qGafkvWI/FMxvEe7OYd5MgbBAuA0kas2lT749c/Gbw8M122e11yuoR92uGM
yUp0lOoGZVb7xwQx7vjxPYmvme8sYr1I9lxL8sWL6SjnADjZ6Wdw+Cgk0Q69liV3
qTZPhCdqaENwbzI8/jDbMYf+P8gc6bN1puvQvoGImBf1WFVrKX5vwi/3BOq1YSIP
OWn17UPxINMzJRcB2IpLsE7ukJPmTlC/4fcthj4KixHIvLpBi9qVlKBjhuSqNgzr
oPv+GxGmwqzU/CqbQOdzXYAbmF4oZIqmJUytyftIGai8Awfk87Ghug4DtZyK4c23
ToGvAoGBAO+GytOzodcgsfeMyEYxlUY1UPUbGNYLXJWmsc/d58I7yRky+9GTp2Pt
s9HW2MW23Iq7865fB1IQdTN5TDMV45Pq6p+5uO14zl96iR+F7/1+ivlQ63o2z1TN
tLFKFdgmCX3+bQwfuZHbYM2l8M1SLOElzz8iK2KDVVZQjgWWVcnvAoGBAORCXJP0
WjTdczgGuoROWtL4+tcY3m8wgOXyvfP0TTbWNPEmswN2GC1JqLFoq1qX+OLbB4ky
5UfclTZGytRqdE/1Metf11ImyxynLHZk4BU4Oqv2vEB6jzZq1PcQ3zHlE9qE+k8u
r8OFsIklDigoIYJoVD4osc/VHpWKBNJr3j0bAoGBALjHEX69xf26IuOJ3FNoFBGW
2A2J7pZ9yxRcBYMY5fw8v7Rah77uP00WdMZyifebsXJWeidt4RNryCBk4wLWXxpW
IrW7KEIp/kmnq5v5m+DPVUP8mGWX/wbn1IjEH3rbg6pWjqLz5uzcbz+Oo9GXKe+D
kT9U36PEZmcoMwuf28epAoGBAJyFRsvawYNWBd1GcUTIA8Pd7dVS4atUdaT+ORxP
v+sWirP9R41YSxe9ev1PFmoBzzx47zmB/E6IoNTC1DnimOZe/ai2v4jKJOByoiVM
fGZScV/5paiOjhavp/nfrv2kZWKkU96GaeUoeQ2VwJCQjAGmoCqfj974igAkIJBJ
93pbAoGAOqVdfaUTSvHuBPhpyAInVqS8j4C/T/tdvMxsn8fQHC01kE6OOqrxPV5R
PrAtME9H1kKmRf0RUzXWrkbnmd+qfvm91uUwVL0cxC+7eMqe7uQQbpOiAPouhiYj
gGr4rmFN9PX9DHGzMhmEBjhP6YycXAsIYPumkqJCVrEMetxuhns=
-----END RSA PRIVATE KEY-----'''

TEST_PUB_KEY = ('ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA1ZIkA7Z735y'
'OLh0Es+gUPjwBa0BBx++lf/PwbNisl+YUc9smve0oGJRUnS9v3EQLEoffDklH7D'
'S2bIZm9K17LEGllLKF6D9i/WR4/7ruS2oZl54cSuwnbzAPLxxFJuJW7dF6nUo0i'
'AjD/su2jPL3WGpvRHxOnDA6QVag0lbqzznZMdtgqUSmM3ErNEN0S+IydFXuoZYg'
'dKte0qEoD6stk9d4HPJpvlc5Dfw2kA07SQ4lnlEpHPoPSsRxAvkdDpEnG8QB1Q2'
'J1etxB6xlOVe/K1e6j+08pBpqeC1mwPHGgCneIdwASh+J1e1rMkLYZs0ZdJGuxQ'
'HlyYBqYetDTmw/NQ==')


class SimpleGitServer(SSHFactory):
    portal = Portal(GitRealm())

    mockpasswd = InMemoryUsernamePasswordDatabaseDontUse()
    mockpasswd.addUser('user', 'user')
    portal.registerChecker(mockpasswd)

    def __init__(self):
        self.privateKeys = {'ssh-rsa': Key.fromString(TEST_PRIV_KEY)}
        self.publicKeys = {'ssh-rsa': Key.fromString(TEST_PUB_KEY)}


if __name__ == '__main__':
    components.registerAdapter(SimpleGitSession, GitConchUser, ISession)
    reactor.listenTCP(2222, SimpleGitServer())
    reactor.run()