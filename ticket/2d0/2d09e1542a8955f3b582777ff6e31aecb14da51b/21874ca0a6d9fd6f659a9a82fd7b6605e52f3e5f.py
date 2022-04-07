
# dns_test.py - simple DNS tester
#
# this program just generates DNS lookups for a non-existent host
# unfortunately it leaves a UDP socket open for every request
#
# on Linux you can see the socket count increase via: lsof -i -nP | grep UDP | wc -l
# on Windows it runs out of file descriptors after a period

from twisted.internet import defer, reactor
from twisted.python.failure import Failure
import twisted.names.client

def next_lookup(count):
    domain = 'aa%06d.com' % count
    d = twisted.names.client.getHostByName(domain, timeout=[1])
    d.addBoth(lookup_done, count)

def lookup_done(result, count):
    print result
    reactor.callLater(2.0, next_lookup, count + 1)
    
reactor.callLater(0, next_lookup, 0)
reactor.run()
