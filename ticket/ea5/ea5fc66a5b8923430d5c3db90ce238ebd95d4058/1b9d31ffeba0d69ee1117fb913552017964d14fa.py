from zope.interface import implements

from twisted.cred import portal
from twisted.cred.credentials import IUsernamePassword, ISSHPrivateKey
from twisted.cred.checkers import ICredentialsChecker

from twisted.conch import manhole_ssh

from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor




class NullChecker(object):

    credentialInterfaces = IUsernamePassword, ISSHPrivateKey
    implements(ICredentialsChecker)

    def requestAvatarId(self, credentials):
        return '1'


class ExecSession(manhole_ssh.TerminalSession):

    def execCommand(self, proto, cmd):
        print "don't want to exec", cmd
        proto.loseConnection()


realm = manhole_ssh.TerminalRealm()
realm.sessionFactory = ExecSession

portal = portal.Portal(realm)

checker = NullChecker()
portal.registerChecker(checker)

endpoint = TCP4ServerEndpoint(reactor, 10022)
endpoint.listen(manhole_ssh.ConchFactory(portal))

reactor.run()
