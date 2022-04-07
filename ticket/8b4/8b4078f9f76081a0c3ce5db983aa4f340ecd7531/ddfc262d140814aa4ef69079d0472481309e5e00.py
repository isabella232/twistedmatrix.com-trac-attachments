# -*- Python -*-

"""Example of rate-limiting your web server.

Caveat emptor: While the transfer rates imposed by this mechanism will
look accurate with wget's rate-meter, don't forget to examine your network
interface's traffic statistics as well.  The current implementation tends
to create lots of small packets in some conditions, and each packet carries
with it some bytes of overhead.  Check to make sure this overhead is not
costing you more bandwidth than you are saving by limiting the rate!
"""

from twisted.protocols import htb
from twisted.internet import protocol
# for picklability
import shaper

serverFilter = htb.HierarchicalBucketFilter()
serverBucket = htb.Bucket()

# Cap total server traffic at 20 kB/s
serverBucket.maxburst = 20000
serverBucket.rate = 20000

serverFilter.buckets[None] = serverBucket

# service is also limited per-peer:
class ClientBucket(htb.Bucket):
    # Your first 10k is free
    maxburst = 10000
    # One kB/s thereafter.
    rate = 1000

clientFilter = htb.FilterByHost(serverFilter)
clientFilter.bucketFactory = shaper.ClientBucket

class Spew(protocol.Protocol):

    def makeConnection(self, transport):
        self.transport = transport
        self.total = 2**25

        def spewing(data):
            self.transport.write(data)
            self.total -= len(data)
            if self.total > 0:
                reactor.callLater(0, spewing, "hello" * 80)

        spewing("hello" * 80)

from twisted.internet.protocol import ServerFactory
site = ServerFactory()
site.protocol = Spew
site.protocol = htb.ShapedProtocolFactory(site.protocol, clientFilter)

from twisted.internet import reactor
reactor.listenTCP(8000, site)
reactor.run()
