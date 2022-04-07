from twisted.protocols import ftp
from twisted.protocols import basic
from twisted.internet.protocol import ClientCreator
from twisted.internet import defer
from twisted.internet import reactor

class FTPClient(ftp.FTPClient):
    def sendFile(self, fileObj, remotepath):
        def _sendFile(sender):
            dconn = basic.FileSender().beginFileTransfer(fileObj, sender.transport)
            dconn.addCallback(lambda _: sender.finish())
        def _closeEverything(deferredlist, d):
            success, result = deferredlist[-1]
            if not success:
                d.errback(result)
                return
            d.callback(result)
        d = defer.Deferred()
        d1, control = self.stor(remotepath)
        d1.addCallback(_sendFile)
        control.addCallback(_closeEverything, d)
        return d

def sendFile(host, port, username, password, passive, fileObj, remotepath):
    creator = ClientCreator(reactor, FTPClient, username, password, passive)
    return creator.connectTCP(host, port
        ).addCallback(_connectionMade, fileObj, remotepath)
        
def _connectionMade(client, fileObj, remotepath):
    return client.sendFile(fileObj, remotepath)

# Usage example
d = sendFile('ftpspace.tin.it', 21, 'dialton3@virgilio.it', 'XXXXXX', 0,
        file('../image.tiff', 'rb'), 'image.tiff')

def back(r):
    print r
    reactor.stop()

d.addCallback(back)
d.addErrback(back)

reactor.run()