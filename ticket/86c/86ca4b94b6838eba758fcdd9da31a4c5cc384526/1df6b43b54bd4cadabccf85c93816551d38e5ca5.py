from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from twisted.protocols import amp

# Server
class CdPlay(amp.Command):
    requiresAnswer = False
    
class CdControlProtocol(amp.AMP):
    def play(self):
        pass
    CdPlay.responder(play)
    
    
d = ClientCreator(reactor, amp.AMP).connectTCP('127.0.0.1', 8080)
d.addCallback(lambda p: p.callRemote(CdPlay))

# Tac stuff
from twisted.application import internet, service
from twisted.internet.protocol import Factory

application = service.Application('CdRemoteControl')
factory = Factory()
factory.protocol = CdControlProtocol
cdService = internet.TCPServer(8080, factory)
cdService.setServiceParent(application)