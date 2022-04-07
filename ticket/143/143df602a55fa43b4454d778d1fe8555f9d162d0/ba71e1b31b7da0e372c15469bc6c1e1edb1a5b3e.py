import unittest
import sys
#sys.path.insert(1,"/home/linlove/workspace/twistedcheckout/trunk/")
from twisted.spread import pb, jelly
from twisted.internet import reactor

class Pond:
  def setRemote(self,remote):
    self.remote=remote
    pass

class Receiver(pb.Root):
    def remote_takePond(self, pond):
        print " got pond:", pond
        pond.remote.callRemote("takePond2",Pond()).addCallback(self.ok).addErrback(self.notOk)
        return "safe and sound" # positive acknowledgement
    
    def ok(self, response):
        print "pond arrived2", response
        reactor.stop()
    def notOk(self, failure):
        print "error during takePond2:"
        if failure.type == jelly.InsecureJelly:
            print " InsecureJelly2"
        else:
            print failure
        return None
        reactor.stop()
  
class Sender(pb.Referenceable):
    def __init__(self, pond):
        self.pond = pond
    def remote_takePond2(self, pond):
        print " got pond2:", pond
    def got_obj(self, obj):
        d = obj.callRemote("takePond", self.pond)
        d.addCallback(self.ok).addErrback(self.notOk)
    def ok(self, response):
        print "pond arrived", response
    def notOk(self, failure):
        print "error during takePond:"
        if failure.type == jelly.InsecureJelly:
            print " InsecureJelly"
        else:
            print failure
        return None
        reactor.stop()



class PBWithSecurityOptionsTest(unittest.TestCase):

    def testSecOptions(self):
      import copy
      gs=copy.copy(jelly.globalSecurity)
      gs.isModuleAllowed=jelly.DummySecurityOptions().isModuleAllowed
      gs.isClassAllowed=jelly.DummySecurityOptions().isClassAllowed
      gs.isTypeAllowed=jelly.DummySecurityOptions().isTypeAllowed

      factory = pb.PBClientFactory(gs)
      serverFactory=pb.PBServerFactory(Receiver(),security=gs)
      reactor.connectTCP("localhost", 8801, factory)
      deferred = factory.getRootObject()
      p=Pond()
      sender = Sender(p)
      p.setRemote(sender)
      deferred.addCallback(sender.got_obj)
      reactor.listenTCP(8801, serverFactory)
      reactor.run()

if __name__ == "__main__":
  unittest.main()
