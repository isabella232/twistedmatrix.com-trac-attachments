from twisted.cred import checkers, credentials

def convo(*a):
    print 'convo', a
    return succeed([("foo", 0) for x in range(len(a))])


creds = credentials.PluggableAuthenticationModules("exarkun", convo)
checker = checkers.PluggableAuthenticationModulesChecker()

from twisted.internet.defer import inlineCallbacks
from twisted.python import log

@inlineCallbacks
def go():
    try:
        avatarId = yield checker.requestAvatarId(creds)
    except Exception, e:
        print 'Error', e
    else:
        print 'avatarId', avatarId
    reactor.stop()

from twisted.internet import reactor
reactor.callWhenRunning(go)
reactor.run()
