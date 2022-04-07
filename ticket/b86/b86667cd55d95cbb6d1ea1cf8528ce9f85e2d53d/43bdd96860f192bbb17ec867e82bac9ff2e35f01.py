from pprint import pprint

from twisted.python import log
from twisted.protocols.ftp import FTPClient, FTPFileListProtocol
from twisted.internet.protocol import ClientCreator
from twisted.internet import reactor

def go(cc):
    d = cc.connectTCP('localhost', 2121)
    def cbConnected(proto):
        lister = FTPFileListProtocol()
        d = proto.list('.', lister)
        d.addCallback(lambda ign: lister.files)
        return d
    d.addCallback(cbConnected)
    def cbFiles(files):
        pprint(files)
    d.addCallback(cbFiles)
    d.addErrback(log.err)
    return d


def main():
    cc = ClientCreator(
        reactor, FTPClient, 'anonymous', 'exarkun@twistedmatrix.com')
    def f(ignored=None):
        d = go(cc)
        d.addCallback(f)
        return d
    f()
    reactor.run()

main()

    