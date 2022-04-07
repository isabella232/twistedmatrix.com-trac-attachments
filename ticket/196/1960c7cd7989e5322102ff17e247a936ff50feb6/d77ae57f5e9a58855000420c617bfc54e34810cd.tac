import os

from twisted.application import service, internet
from twisted.names import dns
from twisted.names import server

from names_test import TestResolver

import names_test

def getService():
  from twisted.names import cache
  ca, cl = [], []

  cl.append(TestResolver())
  f = server.DNSServerFactory([], ca, cl, 1)
  p = dns.DNSDatagramProtocol(f)
  f.noisy = 0
  ret = service.MultiService()
  for (klass, arg) in [(internet.TCPServer, f), (internet.UDPServer, p)]:
      s = klass(5555, arg)
      s.setServiceParent(ret)
  return ret

application = service.Application("names test")

service = getService()
service.setServiceParent(application)
