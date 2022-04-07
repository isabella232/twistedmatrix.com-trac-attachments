from twisted.internet.protocol import Protocol, Factory, ClientFactory

from random import random

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

def give_me_data():
    return ["*" * 90000000] * 10

class Spew(Protocol):

    def spew_time(self):
        #no need for a mutex, since it's single-threaded
        self.factory.writing = 1
        l = len(self.factory.important_data)
        for s in self.factory.important_data:
            assert l == len(self.factory.important_data)
            self.transport.write(s)
        self.factory.writing = 0

    def connectionLost(self, reason):
        print "connectionLost"
        if (random() > 0.5):
            self.factory.important_data.pop(0)
        else:
            self.factory.important_data.append(give_me_data())
        if self.factory.writing:
            print "Connection lost inside transport.write()!"
        self.l.stop()

    def connectionMade(self):
        print "connectionMade"
        self.l = task.LoopingCall(self.spew_time)
        self.l.start(0.1)


class Die(Protocol):
    def connectionMade(self):
        reactor.callLater(random(), self.transport.loseConnection)

clientfactory = ClientFactory()
clientfactory.protocol = Die

l = task.LoopingCall(reactor.connectTCP, '127.0.0.1', 8007, clientfactory)
l.start(1)

factory = Factory()
factory.protocol = Spew
factory.writing = 0
factory.important_data = give_me_data()

# 8007 is the port you want to run under. Choose something >1024
reactor.listenTCP(8007, factory)
reactor.run()
