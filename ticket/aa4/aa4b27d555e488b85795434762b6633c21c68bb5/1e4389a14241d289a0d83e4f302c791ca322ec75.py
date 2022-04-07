# twisted.web.client.py

class HTTPCacheDownloader(HTTPPageGetter):
    def connectionMade(self, isCached=False):
        method = getattr(self.factory, 'method', 'GET')
        self.sendCommand(method, self.factory.path)
        self.sendHeader('Host', self.factory.headers.get("host", self.factory.host))
        self.sendHeader('User-Agent', self.factory.agent)
        
        if self.factory.isCached:
            self.sendHeader('If-None-Match', self.factory.headers.get("etag", '') )
            self.sendHeader('If-Modified-Since',
                    self.factory.headers.get("if-modified-since", '') )
            
        if self.factory.cookies:
            l=[]
            for cookie, cookval in self.factory.cookies.items():  
                l.append('%s=%s' % (cookie, cookval))
            self.sendHeader('Cookie', '; '.join(l))
        data = getattr(self.factory, 'postdata', None)
        if data is not None:
            self.sendHeader("Content-Length", str(len(data)))
        for (key, value) in self.factory.headers.items():
            if key.lower() != "content-length":
                # we calculated it on our own
                self.sendHeader(key, value)
        self.endHeaders()
        self.headers = {}
        
        if data is not None:
            self.transport.write(data) 

    def handleResponse(self, response):
        re = self.headers.get("etag", None)
        rl = self.headers.get("last-modified", None)
        rd = self.headers.get("date", None)
        if re or rl or rd:
            cache = {'response':response}
            if re:
                cache.update({'etag':re})
            if rl and rd:
                cache.update({'if-modified-since':rl})
            elif rd and not rl:
                cache.update({'if-modified-since':rd})
            self.factory.cache[self.factory.url] = cache                 
        HTTPPageGetter.handleResponse(self, response)
        
    def handleStatus_304(self):
        cache_entry = self.factory.cache.get(self.factory.url, None)
        if not cache_entry:
            self.factory.noPage(
                failure.Failure(
                    error.Error(
                        self.status, self.message, "Page missing in cache")))
            self.transport.loseConnection()
        self.handleResponse(cache_entry.get('response'))


class HTTPClientCacheFactory(HTTPClientFactory):

    protocol = HTTPCacheDownloader
    cache = {}
    isCached = False

    def __init__(self, url, method='GET', postdata=None, headers=None,
                 agent="Twisted PageGetter", timeout=0, cookies=None,
                 followRedirect=1):
        headers = {}
        cached = self.cache.get(url, None)
        if cached:
            self.isCached = True
            etag = cached.get('etag', None)
            if_modified_since = cached.get('if-modified-since', None)
            if etag:
                headers.setdefault('etag', etag)
            if if_modified_since:
                headers.setdefault('if-modified-since', if_modified_since)
        else:
            self.isCached = False

        HTTPClientFactory.__init__(self, url=url, method=method,
                postdata=postdata, headers=headers, agent=agent,
                timeout=timeout, cookies=cookies, followRedirect=followRedirect)
        self.deferred = defer.Deferred()

def getPageCached(url, contextFactory=None, *args, **kwargs):
    """download a web page as a string, keep a cache of already downloaded pages

    Download a page. Return a deferred, which will callback with a
    page (as a string) or errback with a description of the error.

    See HTTPClientCacheFactory to see what extra args can be passed.
    """       
    scheme, host, port, path = _parse(url)
    factory = HTTPClientCacheFactory(url, *args, **kwargs)
    if scheme == 'https':
        from twisted.internet import ssl
        if contextFactory is None:
            contextFactory = ssl.ClientContextFactory()
        reactor.connectSSL(host, port, factory, contextFactory)
    else:
        reactor.connectTCP(host, port, factory)
    return factory.deferred
    
#
# Tests for tests_webclient.py
#

    def testGetPageCached(self):
        self.assertEquals(unittest.deferredResult(client.getPageCached(self.getURL("file"))),
                          "0123456789")



    def testTimeoutCached(self):
        r = unittest.deferredResult(client.getPageCached(self.getURL("wait"), timeout=1.5))
        self.assertEquals(r, 'hello!!!')
        f = unittest.deferredError(client.getPageCached(self.getURL("wait"), timeout=0.5))
        f.trap(defer.TimeoutError)
