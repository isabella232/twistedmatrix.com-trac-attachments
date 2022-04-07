class _DummyController:
    def messageReceived(self, *args):
        pass

class Resolver(common.ResolverBase):
    def __init__(self, hints):
        common.ResolverBase.__init__(self)
        self.hints = hints

    def _lookup(self, name, cls, type, timeout):
        d = discoverAuthority(name, self.hints
            ).addCallback(self.discoveredAuthority, name, cls, type, timeout
            )
        return d

    def discoveredAuthority(self, auth, name, cls, type, timeout):
        from twisted.names import client
        q = dns.Query(name, type, cls)
        r = client.Resolver(servers=[(auth, dns.PORT)])
        d = r.queryUDP([q], timeout)
        d.addCallback(r.filterAnswers)
        return d

def lookupNameservers(host, atServer, p=None):
    # print 'Nameserver lookup for', host, 'at', atServer, 'with', p
    if p is None:
        p = dns.DNSDatagramProtocol(_DummyController())
        p.noisy = False
    return retry(
        (1, 3, 11, 45),                     # Timeouts
        p,                                  # Protocol instance
        (atServer, dns.PORT),               # Server to query
        [dns.Query(host, dns.NS, dns.IN)]   # Question to ask
    )

def lookupAddress(host, atServer, p=None):
    # print 'Address lookup for', host, 'at', atServer, 'with', p
    if p is None:
        p = dns.DNSDatagramProtocol(_DummyController())
        p.noisy = False
    return retry(
        (1, 3, 11, 45),                     # Timeouts
        p,                                  # Protocol instance
        (atServer, dns.PORT),               # Server to query
        [dns.Query(host, dns.A, dns.IN)]    # Question to ask
    )
