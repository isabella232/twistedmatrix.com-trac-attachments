from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from twisted.protocols import amp
from gridnode.amp.fileTransferAmpServer import FileTransfer

class Client(object):
    def __init__(self, clientIp , clientPort ):
        self._proto = None
        self._clientIp = clientIp
        self._clientPort = clientPort
        creator = ClientCreator(reactor, amp.AMP)
        creator.connectTCP(self._clientIp, self._clientPort).addCallback( self.cbOkStartClient)
 
    
    def cbOkStartClient(self,proto):
        self._proto = proto
        self.startClient()



class GridClient(Client):
    
    def __init__(self, ip, port):
        Client.__init__(self, ip, port)
        
    
    def startClient(self ):
        print "in pfun"
        
        d = self._proto.callRemote(FileTransfer, filename="myFileName.txt")
        d.addCallback(self.cbOkProcessResult)
        

    def cbOkProcessResult(self,result):

        contents= result['contents']
        print "process result"
        print "results = ", contents
        
        reactor.stop()
        return result        
 
g = GridClient('127.0.0.1', 1234)
 
            
reactor.run()
