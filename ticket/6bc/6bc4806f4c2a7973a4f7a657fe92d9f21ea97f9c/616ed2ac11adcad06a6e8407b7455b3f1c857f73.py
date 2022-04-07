from twisted.internet.protocol import Protocol,ClientFactory, ServerFactory
from twisted.protocols.basic import FileSender
from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor
import gtk

win = gtk.Window()
win.set_size_request(300,300)
lab = gtk.Label("Hello")
win.add(lab)
win.show_all()

class Producer(object):
    def read(self,size=1):
        return "1"*size


class Client(Protocol):
    def connectionMade(self):
        fs = FileSender()
        pr = Producer()
        fs.beginFileTransfer(pr, self.transport)


class Server(Protocol):

    def dataReceived(self, data):
        pass

    
cf = ClientFactory()
cf.protocol = Client
sf = ServerFactory()
sf.protocol = Server
reactor.listenTCP(10000, sf)
reactor.connectTCP("localhost",10000,cf)

reactor.run()
