from twisted.application import internet
from twisted.application.service import Application
from twisted.protocols import amp

from twisted.cred.portal import Portal
from twisted.conch.ssh.factory import SSHFactory
from twisted.conch.ssh.keys import Key
from twisted.conch.interfaces import IConchUser
from twisted.conch.avatar import ConchUser
from twisted.internet.protocol import Protocol
from twisted.conch.ssh.session import (
    SSHSession, SSHSessionProcessProtocol, wrapProtocol)

class Echoer(Protocol):
    def connectionMade(self):
        self.transport.write("Echo protocol connected\r\n")

    def dataReceived(self, bytes):
        self.transport.write("echo: " + repr(bytes) + "\r\n")

    def connectionLost(self, reason):
        print 'Connection lost', reason


class AMPSession(SSHSession):
    name = 'session'

    def request_pty_req(self, data):
        # ignore pty requests
        return True

    def request_shell(self, data):
        protocol = amp.AMP()
        #protocol = Echoer()

        transport = SSHSessionProcessProtocol(self)
        transport.getPeer = lambda:'FAKE'
        transport.getHost = lambda:'FAKE'
        protocol.makeConnection(transport)
        transport.makeConnection(wrapProtocol(protocol))
        self.client = transport
        return True


class SimpleRealm(object):
    def requestAvatar(self, avatarId, mind, *interfaces):
        u = ConchUser()
        u.channelLookup['session'] = AMPSession
        return IConchUser, u, lambda:None


# generate you a key with: ckeygen -f id_rsa -t rsa
with open('id_rsa') as privateBlobFile:
    privateBlob = privateBlobFile.read()
    privateKey = Key.fromString(data=privateBlob)

with open('id_rsa.pub') as publicBlobFile:
    publicBlob = publicBlobFile.read()
    publicKey = Key.fromString(data=publicBlob)


application = Application('testapp')

factory = SSHFactory()
factory.privateKeys = {'ssh-rsa': privateKey}
factory.publicKeys = {'ssh-rsa': publicKey}
factory.portal = Portal(SimpleRealm())

from zope.interface import implements
from twisted.cred.checkers import ICredentialsChecker
from twisted.cred import credentials
class TSAAgent:
    implements(ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,)
    def requestAvatarId(self, c):
        return 'OK'

# checks keys against the authorized_keys file of the user
# requesting login.
factory.portal.registerChecker(TSAAgent())

ssh = internet.TCPServer(2222, factory)
ssh.setServiceParent(application)

