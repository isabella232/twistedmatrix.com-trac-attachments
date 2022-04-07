from twisted.protocols import amp
from time import sleep

class FileTransfer(amp.Command):
    arguments = [('fileName', amp.String())]
    response = [('contents', amp.String())]

class DataGridNode(amp.AMP):
    def transferFile(self, fileName):
        contents="These are my File Contents"
        print 'reading file', fileName
        return {'contents': contents}
    FileTransfer.responder(transferFile)

def main():
    from twisted.internet import reactor
    from twisted.internet.protocol import Factory
    pf = Factory(); pf.protocol = DataGridNode
    reactor.listenTCP(1234, pf)
    print 'started'
    reactor.run()

if __name__ == '__main__':
    main()
