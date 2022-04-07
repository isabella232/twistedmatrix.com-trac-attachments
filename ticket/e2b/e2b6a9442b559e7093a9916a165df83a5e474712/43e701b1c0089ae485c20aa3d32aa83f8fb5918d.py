from twisted.internet.protocol import Protocol, Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import ClientFactory
from twisted.internet import reactor

import threading, time

def log( st ):
    print "%s %s" % (time.asctime(), st) 

# This is just about the simplest possible protocol
class Echo(Protocol):
    def dataReceived(self, data):
        """As soon as any data is received, write it back."""
        log( "echo %s" % data )
        self.transport.write(data)


class EchoClient(LineReceiver):
    end="Bye-bye!"
    def connectionMade(self):
        log( "connectionMade" )
        self.sendLine("Hello, world!")
        self.sendLine("What a fine day it is.")
        self.sendLine(self.end)

    def lineReceived(self, line):
        log( "receive: %s" % line )
        if line==self.end:
            self.transport.loseConnection()

class EchoClientFactory(ClientFactory):
    protocol = EchoClient

    def clientConnectionFailed(self, connector, reason):
        log( 'connection failed: %s' % reason.getErrorMessage() )
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        log( 'connection lost: %s'% reason.getErrorMessage())
        reactor.stop()

echo_client_factory = EchoClientFactory()

def work_cherrypy():
    while True:
        to = time.time() + 5
        while to > time.time():
            # sleep maybe interrupted
            time.sleep( 1 )

        #create tcp connection
        df = reactor.connectTCP('localhost', 8000, echo_client_factory)
        log( "connectTCP")

def do_nothing():
    reactor.callLater( 30, do_nothing )

def main():
    # start echo server
    f = Factory()
    f.protocol = Echo
    reactor.listenTCP(8000, f)

    # start worker thread - this is the source of cherrypy/turbogears requests
    wthread = threading.Thread( target=work_cherrypy )
    wthread.setDaemon(True)
    wthread.start()

    reactor.callLater( 30, do_nothing )
    reactor.run()

main()
