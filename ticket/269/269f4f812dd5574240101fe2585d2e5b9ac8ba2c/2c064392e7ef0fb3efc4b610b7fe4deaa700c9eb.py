from twisted.internet import reactor, defer, protocol
from twisted.conch.ssh import connection, filetransfer, keys, userauth
from twisted.conch.ssh import channel, transport, common
from twisted.conch.client import options, default, connect
from twisted.python import log, failure
import sys

# Set these.
publicKey = 'public key'
privateKey = 'private key'
passphrase = None
USER = 'username'


def run():
    opts = options.ConchOptions()
    opts['host'] = 'localhost'
    opts['user'] = USER
    opts['port'] = 22
    log.startLogging(sys.stdout)
    log.msg('logging started')
    protocol.ClientCreator(reactor, SimpleTransport).connectTCP(opts['host'], opts['port'])
    reactor.run() # start the event loop


def doConnect(options):
    host = options['host']
    user = options['user']
    port = options['port']
    conn = SSHConnection
    vhk = default.verifyHostKey
    uao = UserAuthClient(user, conn)
    d = connect.connect(host, port, options, vhk, uao)
    d.addErrback(_ebExit)
    return d


def _ebExit(f):
    if hasattr(f.value, 'value'):
        s =f.value.value
    else:
        s = str(f)
    log.msg( s )
    try:
        reactor.stop()
    except:
        pass


def _cleanExit():
    try:
        reactor.stop()
    except:
        pass


class SimpleTransport(transport.SSHClientTransport):
    def verifyHostKey(self, hostKey, fingerprint):
        log.msg('host key fingerprint: %s' % fingerprint)
        return defer.succeed(1)
    def connectionSecure(self):
        self.requestService(
            UserAuthClient(USER,
                SSHConnection()))


class UserAuthClient(userauth.SSHUserAuthClient):
    """Simple User Authentication Client"""
    def getPassword(self, prompt = None):
        return
        # this says we won't do password authentication

    def getPublicKey(self):
        return keys.Key.fromString(publicKey)

    def getPrivateKey(self):
        return defer.succeed(keys.Key.fromString(privateKey, passphrase=passphrase))


class SSHConnection(connection.SSHConnection):
    def serviceStarted(self):
        log.msg('Service started')
        self.openChannel(SSHSession(conn = self))


class SSHSession(channel.SSHChannel):
    name = 'session'
    def channelOpen(self, irgnoreData):
        log.msg('session %s is open' % self.id)
        request = 'subsystem'
        d = self.conn.sendRequest(self, request, common.NS('sftp'), wantReply=1)
        d.addCallback(self._cbSubsystem)
        d.addErrback(_ebExit)
        return d

    def _cbSubsystem(self, result):
        log.msg('Establishing Subsystem')
        self.client = SFTPClient()
        self.client.makeConnection(self)
        self.dataReceived = self.client.dataReceived

    def openFailed(self, reason):
        log.err('Opening Session failed: %s' % reason)
        _cleanExit()


class SFTPClient(filetransfer.FileTransferClient):
    def __init__(self):
        filetransfer.FileTransferClient.__init__(self)
        self.currentDirectory = ''

    def connectionMade(self):
        log.msg('Connection with SFTPClient established')
        self.realPath('').addCallback(self._cbSetCurDir).addErrback(_cleanExit)

    def _cbSetCurDir(self, path):
        self.currentDirectory = path
        log.msg('currentDirectory set to %s.' % path)
        #self.cmd_MKDIR('test')
        self.cmd_LS(self.currentDirectory)

    def cmd_MKDIR(self, path):
        return self.makeDirectory(path, {}).addCallback(self._ignore)

    def cmd_LS(self, path):
        log.msg('List Stucture of %s' % path)
        d = self.openDirectory(path)
        d.addCallback(self._cbOpenList)

    def _cbOpenList(self, directory):
        files = []
        log.msg('direc.:%s' % str(directory))
        log.msg('direc.:%s' % type(directory))
        log.msg('direc.:%s' % str(directory.parent))
        log.msg('direc.:%s' % type(directory.parent))
        d = directory.read()
        d.addCallback(self._cbReadFile, files, directory)
        d.addErrback(self._ebReadFile, files, directory)

    def _ebReadFile(self, files, l, directory):
        log.msg('**errback!**')
        self._cbReadFile(files, l, directory)

    def _cbReadFile(self, files, l, directory):
        log.msg('ReadFile called')
        log.msg('direc.:%s' % type(files))
        if not isinstance(files, failure.Failure):
            log.msg('if not')
            l.extend(files)
            d = directory.read()
            #d.addCallback(self._ignore)
            d.addBoth(self._cbReadFile, l, directory)
            return d
        else:
            log.msg('else')
            reason = files
            reason.trap(EOFError)
            directory.close()
            return l

    def _ignore(self, *args):
        pass


if __name__ == "__main__":
    run()
