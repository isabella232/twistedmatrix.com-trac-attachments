from twisted.internet.protocol import Protocol, Factory, ClientFactory

from random import randint
from cStringIO import StringIO
from traceback import print_exc

import os
if os.name == 'nt':
    try:
        from twisted.internet import iocpreactor
        iocpreactor.proactor.install()
    except:
        pass
else:
    try:
        from twisted.internet import pollreactor
        pollreactor.install()
    except:
        pass

#the default reactor is select-based, and will be install()ed if another has not    
from twisted.internet import reactor, task

class Spew(Protocol):

    def connectionLost(self, reason):
        print "connectionLost: " + str(reason)

    def connectionMade(self):
        print "connectionMade:" + str(self.transport.getPeer())
        self.buffer = OutputBuffer(self)
        self.buffer.signal()

class Eat(Protocol):

    def dataReceived(self, data):
        print data

class OutputBuffer(object):

    def __init__(self, connection):
        self.connection = connection
        self.consumer = None

    def signal(self):
        if self.consumer is None:
            self.beginWriting()

    def beginWriting(self):
        self.stopWriting()
        self.consumer = self.connection.transport
        self.consumer.registerProducer(self, False)

    def stopWriting(self):
        if self.consumer is not None:
            self.consumer.unregisterProducer()
        self.consumer = None

    def resumeProducing(self):
        if self.consumer is not None:

            r = randint(-1, 5)
            if r > -1:
                s = '*' * r
                n = str(r)
                
                print "Writing " + n
                self.consumer.write(s)
            else:
                print "Writing Nothing"

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass
            

clientfactory = ClientFactory()
clientfactory.protocol = Eat

factory = Factory()
factory.protocol = Spew

# 8007 is the port you want to run under. Choose something >1024
reactor.listenTCP(8007, factory)

reactor.connectTCP('127.0.0.1', 8007, clientfactory)

reactor.run()
