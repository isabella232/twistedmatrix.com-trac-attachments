from twisted.internet import reactor
from twisted.spread import pb
from twisted.cred import credentials

def onConnected(self, avatar):
    reactor.stop()

def onError(self, err):
    reactor.stop()

factory = pb.PBClientFactory()
# Assuming a pb server is running on localhost:7777
reactor.connectTCP('localhost', 7777, factory)
        
d = factory.login(credentials.Anonymous())

# Traceback (most recent call last):
#  File "anonymous.py", line 15, in ?
#    d = factory.login(credentials.Anonymous())
#  File "/usr/lib/python2.2/site-packages/twisted/spread/pb.py", line 1626, in login
#    d.addCallback(self._cbSendUsername, credentials.username, credentials.password, client)
#AttributeError: Anonymous instance has no attribute 'username'

d.addCallback(onConnected)
d.addErrback(onError)

reactor.run()

