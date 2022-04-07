from twisted.names import common, dns
from twisted.python import failure
from twisted.internet import defer

class TestResolver(common.ResolverBase):

  def __init__(self, ttl = 300):
    common.ResolverBase.__init__(self)
    self.ttl = ttl

  def _fail(self, name):
    return defer.fail(failure.Failure(dns.DomainError(name)))

  def lookupZone(self, name, timeout = None):
    records = []
    soa = dns.RRHeader(name='foo', type=dns.SOA, cls=dns.IN, ttl=86400, auth=False,
                                payload=dns.Record_SOA(mname='foo',
                                                       rname='bar',
                                                       serial=100,
                                                       refresh=10,
                                                       retry=10,
                                                       expire=2000,
                                                       minimum=100,
                                                       ttl=100))

    records.append(soa)
    for i in range(0, 2800):
      dname = '%s-%s.%s' % ('foo', i, 'bar.test')
      record = dns.RRHeader(dname, dns.A, dns.IN, self.ttl,
                    dns.Record_A('127.0.0.1', 300))
      records.append(record)

    records.append(soa)

    return defer.succeed([
          records, (), ()
    ])
