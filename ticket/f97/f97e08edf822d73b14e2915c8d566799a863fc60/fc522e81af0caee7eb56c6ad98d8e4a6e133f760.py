    for server in dnsServer:
        resolver = client.Resolver(servers=[(server, 53)])
        for domain in domainList:
                 resolver.getHostByName(domain,effort=1).addCallback(getIPAddress).addErrback(gotError)
