from twisted.trial import unittest
from twisted.spread import pb, jelly

class Receiver(pb.Root):
  pass

class PBWithSecurityOptionsTest(unittest.TestCase):
    def testSecOptions(self):
      import copy
      gs=copy.copy(jelly.globalSecurity)
      gs.isModuleAllowed=jelly.DummySecurityOptions().isModuleAllowed
      gs.isClassAllowed=jelly.DummySecurityOptions().isClassAllowed
      gs.isTypeAllowed=jelly.DummySecurityOptions().isTypeAllowed

      factory = pb.PBClientFactory(gs)
      factory.clientConnectionMade(pb.Broker(0))
      serverFactory=pb.PBServerFactory(Receiver(),security=gs)
      self.assertEquals(gs, factory.security)
      self.assertEquals(gs, factory._broker.security)
      proto = serverFactory.buildProtocol("127.0.0.1")
      self.assertEquals(gs, proto.security)

