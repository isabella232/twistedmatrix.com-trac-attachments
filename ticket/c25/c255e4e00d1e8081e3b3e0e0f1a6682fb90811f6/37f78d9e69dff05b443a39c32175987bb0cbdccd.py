#!/usr/bin/python2.4
from twisted.words.protocols.irc import IRC
from twisted.internet import reactor, protocol, defer
from twisted.python import failure
from twisted.words import iwords, ewords

from twisted.words.service import IRCFactory, WordsRealm, InMemoryWordsRealm
from twisted.cred import portal, checkers, credentials
from zope.interface import implements
import IRCServer

class ApolloProtocol(IRCServer.IRCService):
    def connectionMade(self): 
        print "Hello @ new person.."

class ServerMain:
    def __init__(self, configFile):
        self.configFile = configFile
        pass

    def readConfig(self):
        fi = open(self.configFile).read()
        exec fi

class DontCare:
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = credentials.IUsernamePassword,

    def __init__(self):
        pass

    def requestAvatarId(self, credentials):
        return credentials.username

def createPortal(realm): 
    porta = portal.Portal(realm, [DontCare()])
    checker = DontCare()
    #porta.registerChecker(checker)
    #porta.registerChecker(checkers.AllowAnonymousAccess, credentials.IAnonymous)
    return porta

if __name__ == '__main__':
    realm = IRCServer.IRCRealm("localhost")
    factory = IRCFactory(realm, createPortal(realm))
    factory.protocol = ApolloProtocol
    factory.protocol.realm = realm
    reactor.listenTCP(6667,factory)
    reactor.run()

