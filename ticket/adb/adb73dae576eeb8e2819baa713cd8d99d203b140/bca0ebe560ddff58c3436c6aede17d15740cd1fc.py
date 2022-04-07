

from twisted.internet import defer, reactor
from twisted.python.failure import Failure
import twisted.names.client

def do_lookup(do_lookup):
    d = twisted.names.client.getHostByName(domain)
    d.addBoth(lookup_done)

def lookup_done(result):
    print 'result:', result
    reactor.stop()

domain = 'www.bbc.co.uk'    
reactor.callLater(0, do_lookup, domain)
reactor.run()
