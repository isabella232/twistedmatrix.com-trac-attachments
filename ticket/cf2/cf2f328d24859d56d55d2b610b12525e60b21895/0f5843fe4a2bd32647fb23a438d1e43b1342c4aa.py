
from twisted.protocols import oscar
from twisted.internet import protocol
from twisted.internet import reactor

class A(oscar.BOSConnection):
    capabilities = [oscar.CAP_CHAT]
    
    def initDone(self):
        self.clientReady()

class B(oscar.OscarAuthenticator):
    BOSClass = A

USER = 'xxxx'
PASS = 'xxxx'

cc = protocol.ClientCreator(reactor, B, USER, PASS, icq=False).connectTCP("login.oscar.aol.com", 5190)
reactor.run()
