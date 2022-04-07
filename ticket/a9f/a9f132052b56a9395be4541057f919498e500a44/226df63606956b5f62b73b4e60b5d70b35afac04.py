from twisted.internet.base import ThreadedResolver as _ThreadedResolverImpl

from twisted.web.server import Site, NOT_DONE_YET
from twisted.web.resource import Resource
from twisted.names import dns, client, root, cache, resolve, hosts
from twisted.internet import reactor

from twisted.names.error import DNSFormatError, DNSServerError, DNSNameError
from twisted.names.error import DNSNotImplementedError, DNSQueryRefusedError
from twisted.names.error import DNSUnknownError, DNSQueryTimeoutError

import logging
logging.basicConfig(level=logging.DEBUG)
DNSLogger = logging.getLogger('DNSHTTPServer')

typeToMethod = {
    dns.A:     'lookupAddress',
    dns.AAAA:  'lookupIPV6Address',
    dns.A6:    'lookupAddress6',
    dns.NS:    'lookupNameservers',
    dns.CNAME: 'lookupCanonicalName',
    dns.SOA:   'lookupAuthority',
    dns.MB:    'lookupMailBox',
    dns.MG:    'lookupMailGroup',
    dns.MR:    'lookupMailRename',
    dns.NULL:  'lookupNull',
    dns.WKS:   'lookupWellKnownServices',
    dns.PTR:   'lookupPointer',
    dns.HINFO: 'lookupHostInfo',
    dns.MINFO: 'lookupMailboxInfo',
    dns.MX:    'lookupMailExchange',
    dns.TXT:   'lookupText',

    dns.RP:    'lookupResponsibility',
    dns.AFSDB: 'lookupAFSDatabase',
    dns.SRV:   'lookupService',
    dns.NAPTR: 'lookupNamingAuthorityPointer',
    dns.AXFR:         'lookupZone',
    dns.ALL_RECORDS:  'lookupAllRecords',
}

class BadRequest(Resource):
    def __init__(self, message=''):
        Resource.__init__(self)
        self.message = message
    def render_GET(self, request):
        request.setResponseCode(400)
        return "<html><head><title>Bad Request</title></head><body><center><h1>Bad Request</h1></center></body></html>"

class Nameservice(Resource):
    def render_GET(self, request):
        return BadRequest(request)

class ResolveHere(Resource):
    def __init__(self,queryClass,typeKey):
        Resource.__init__(self)
        self.queryClass = queryClass
        self.typeKey = typeKey
    def getChild(self,path,request):
        return doLookUp(self.queryClass,self.typeKey,path)

    def render_GET(self,request):
        return BadRequest(request)

class doLookUp(Resource):
    def __init__(self,queryClass,typeKey,query):
        Resource.__init__(self)
        self.queryClass = queryClass
        self.typeKey = typeKey
        self.query = query
    def returnResults(self, result, request):
        DNSLogger.debug("RESULTS: %s for REQUEST:%s" % (result,request))
        pickled='dummy'
        DNSLogger.debug("simplejson: %s" % (pickled))
        request.setHeader("Content-Type","application/json")
        request.write("%s" % (pickled))
        request.finish()
    def returnError(self, failure, request):
        error=failure.trap(DNSServerError,DNSNameError,DNSQueryRefusedError,DNSQueryTimeoutError)
        # error=failure.trap(DNSFormatError, DNSServerError, DNSNameError,
        #                    DNSNotImplementedError, DNSQueryRefusedError,
        #                    DNSUnknownError,DNSQueryTimeoutError)
        message=failure.getErrorMessage()
        DNSLogger.critical("FAILURE: %s(%s) for REQUEST: %s" % (error.__name__,message,request))
        if (error==DNSNameError):
            request.setResponseCode(404)
        elif (error==DNSQueryRefusedError):
            request.setResponseCode(403)
        elif (error==DNSQueryTimeoutError):
            request.setResponseCode(408)
        elif (error==DNSServerError):
            request.setResponseCode(502)
        else:
            request.setResponseCode(500)
        request.setHeader("Content-Type","application/json")
        response='[[{"__type__":"error", "class":"%s"}]]' % (error.__name__)
        DNSLogger.debug("FAILURE RESPONSE: %s" % response)
        request.write(response)
        request.finish()

    def cancelRequest(self,failure,deferedCall,request):
        DNSLogger.debug("CANCELED: %s" % (request))
        #deferedCall.cancel()
        #err(failure,"Canceled Request")

    def render_GET(self,request):
        DNSLogger.info("REQUEST: %s" % (request))
        d=theResolver.typeToMethod[self.typeKey](self.query)
        d.addCallback(self.returnResults,request)
        d.addErrback(self.returnError,request)
        #request.notifyFinish().addErrback(self.cancelRequest, d, request)
        return NOT_DONE_YET

theResolver=None
if __name__ == "__main__":
    resolvers=[]
    cacheResolver = cache.CacheResolver(verbose=True)
    resolvers.append(cacheResolver)
    #clientResolver = client.Resolver(servers=[('1.2.3.4',53)])
    hostResolver = hosts.Resolver(file='named.root.txt')
    rootResolver = root.bootstrap(hostResolver)
    resolvers.append(rootResolver)
    #resolvers.append(hostResolver)
    #resolvers.append(clientResolver)
    theResolver = resolve.ResolverChain(resolvers)

    root = Resource()
    NS = Nameservice()
    for (k, v) in dns.QUERY_TYPES.items() + dns.EXT_QUERIES.items():
        try:
            m = typeToMethod[k]
        except KeyError:
            pass
        else:
            NS.putChild(v,ResolveHere(dns.IN,k))
    root.putChild('IN',NS)
    factory = Site(root)
    reactor.listenTCP(7777, factory)
    reactor.run()
