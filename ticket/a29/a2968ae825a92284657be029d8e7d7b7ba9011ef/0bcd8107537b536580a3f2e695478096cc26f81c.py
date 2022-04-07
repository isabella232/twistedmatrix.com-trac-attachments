from sys import stdout

from twisted.python.log import startLogging, err

from twisted.internet import reactor
from twisted.internet.defer import Deferred, succeed

from twisted.conch.ssh.common import NS
from twisted.conch.scripts.cftp import ClientOptions
from twisted.conch.ssh import filetransfer
from twisted.conch.ssh.filetransfer import FileTransferClient
from twisted.conch.client.connect import connect
from twisted.conch.client.default import SSHUserAuthClient, verifyHostKey
from twisted.conch.ssh.connection import SSHConnection
from twisted.conch.ssh.channel import SSHChannel

class ClientUserAuth(SSHUserAuthClient):

    def getPassword(self, prompt = None):
        print "I am not being called!"
        return succeed("************")

    def getPublicKey(self):
        print "I am being called!"
        return 

class SFTPSession(SSHChannel):
    name = 'session'

    def channelOpen(self, whatever):
        d = self.conn.sendRequest(
            self, 'subsystem', NS('sftp'), wantReply=True)
        d.addCallbacks(self._cbSFTP)

    def _cbSFTP(self, result):
        client = FileTransferClient()
        client.makeConnection(self)
        self.dataReceived = client.dataReceived
        self.conn._sftp.callback(client)

class SFTPConnection(SSHConnection):
    def serviceStarted(self):
        self.openChannel(SFTPSession())

def sftp(user, host, port):
    options = ClientOptions()
    options['host'] = host
    options['port'] = port
    conn = SFTPConnection()
    conn._sftp = Deferred()
    auth = ClientUserAuth(user, options, conn)
    connect(host, port, options, verifyHostKey, auth)
    return conn._sftp

def transfer(client,filename,attrs,filestring):
    d = client.openFile(filename, filetransfer.FXF_READ|filetransfer.FXF_WRITE|filetransfer.FXF_CREAT, attrs)

    def _fileWrite(openFile):
        d = _writeChunk(openFile)
        return d

    def _writeChunk(openFile):
        d = openFile.writeChunk(1,filestring)
        print "File sent successfully"
        return d

    d.addCallback(_fileWrite)
    return d

def main():
    startLogging(stdout)

    user = 'user'
    host = 'localhost'
    port = 22
    d = sftp(user, host, port)
    d.addCallback(transfer,"test.dat",{"permissions":33261,},"c"*10)
    d.addErrback(err, "Problem with SFTP transfer")
    d.addCallback(lambda ignored: reactor.stop())
    reactor.run()

if __name__ == '__main__':
    main()

