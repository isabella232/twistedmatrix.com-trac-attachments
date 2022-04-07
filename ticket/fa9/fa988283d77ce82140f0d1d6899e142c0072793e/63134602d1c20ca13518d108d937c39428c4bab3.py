from twisted.internet import reactor,ssl
from twisted.web.client import HTTPClientFactory
import sys

class Test:

  def Start(self):
      self.factory = HTTPClientFactory('https://www.he.net',method='GET')
      contextFactory = ssl.ClientContextFactory()
      reactor.connectSSL('www.he.net', 443, self.factory, contextFactory)
      self.factory.deferred.addCallback(self.Success)
      self.factory.deferred.addErrback(self.Error)
      reactor.run()

  def Success(self,data):
    print "Success: %s " % data
    reactor.stop()

  def Error(self,data):
     print "Error: %s " % data
     reactor.stop()


c = Test()
c.Start()
