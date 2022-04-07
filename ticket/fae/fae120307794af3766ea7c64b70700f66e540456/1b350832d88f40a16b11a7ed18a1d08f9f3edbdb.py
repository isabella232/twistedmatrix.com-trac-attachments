from twisted.internet import defer, protocol, reactor
from twisted.conch.ssh import channel, common, connection, filetransfer
from twisted.conch.ssh import transport, userauth
import getpass

def fatal(failure):
    failure.printTraceback()
    try:
        reactor.crash()
    except RuntimeError:
        pass

class Authenticate(userauth.SSHUserAuthClient):
    def getPassword(self):
        return defer.succeed(getpass.getpass())
    def getGenericAnswers(self, name, instruction, questions):
        print name
        print instruction
        answers = []
        for prompt, echo in questions:
            if echo:
                answer = raw_input(prompt)
            else:
                answer = getpass.getpass(prompt)
            answers.append(answer)
        return defer.succeed(answers)

class SFTPChannel(channel.SSHChannel):
    def __init__(self, conn):
        channel.SSHChannel.__init__(self, conn=conn)
        self.name = 'session'
        self.__conn = conn
    def channelOpen(self, _):
        d = self.__conn.sendRequest(self, 'subsystem', common.NS('sftp'),
                                    wantReply=True)
        d.addCallback(self._subsystemOpen)
        d.addErrback(fatal)
    def _subsystemOpen(self, _):
        self.__client = filetransfer.FileTransferClient()
        self.__client.transport = self
        d = self.__client.openDirectory('/')
        d.addCallbacks(self._directoryOpen, fatal)
    def dataReceived(self, data):
        self.__client.dataReceived(data)
    def _directoryOpen(self, dir):
        self.__dir = dir
        self.__dirIter = iter(dir)
        self._readDirectory()
    def _readDirectory(self):
        d = None
        try:
            while not d:
                entry = self.__dirIter.next()
                if isinstance(entry, defer.Deferred):
                    d = entry
                    d.addCallbacks(lambda *_: self._readDirectory(),
                                   self._readDirectoryFailed)
        except StopIteration:
            self._closeDirectory()
    def _readDirectoryFailed(self, failure):
        if failure.check(EOFError):
            self._closeDirectory()
        else:
            fatal(failure)
    def _closeDirectory(self):
        self.__dir.close()
        self.__conn.transport.loseConnection()

class SFTPConnection(connection.SSHConnection):
    def serviceStarted(self):
        connection.SSHConnection.serviceStarted(self)
        self.__channel = self.openChannel(SFTPChannel(self))

class Transport(transport.SSHClientTransport):
    def __init__(self, user):
        self.__user = user
        self.__connection = SFTPConnection()
    def verifyHostKey(self, *_):
        return defer.succeed(True)
    def connectionSecure(self):
        self.requestService(Authenticate(self.__user, self.__connection))

class Factory(protocol.ClientFactory):
    def __init__(self, user):
        self.__user = user
    def buildProtocol(self, addr):
        return Transport(self.__user)
    def clientConnectionLost(self, connector, reason):
        fatal(reason)
    def clientConnectionFailed(self, connector, reason):
        fatal(reason)

if __name__ == '__main__':
    import sys
    host, user = sys.argv[1:3]
    reactor.connectTCP(host, 22, Factory(user), 30)
    reactor.run()
