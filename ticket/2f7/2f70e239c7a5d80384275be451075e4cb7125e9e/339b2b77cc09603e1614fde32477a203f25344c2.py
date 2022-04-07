#!/usr/bin/python
import twisted.python.urlpath, urlparse, twisted.web.proxy
"""proxymap.py: More powerful reverse-proxy setup for twisted.web.

As documented in http://twistedmatrix.com/bugs/issue1109
"twisted.web.proxy doesn't reverse-map redirects like
ProxyPassReverse", reverse proxies need to rewrite HTTP redirect URLs,
and rewriting redirects in a reverse proxy requires knowledge of more
than just a single ReverseProxyResource.

This code makes such a setup easy to configure.  You create a ProxyMap
object and hand your root Resource to its createMappings method:

    p = ProxyMap({'/foo': 'http://localhost:8000/f00',
                  '/slash': 'http://localhost:8100/slash/',
                  '/slush/': 'http://localhost:8100/slush',
                  '/bar': 'http://localhost/b4r',
                  '/baz/quux': 'http://localhost:8000/quux'})

    r.putChild('slush', twisted.web.resource.Resource())
    r.putChild('baz', twisted.web.resource.Resource())
    p.createMappings(r)

If there are intermediate resources that must be created, you must
create them yourself.  They probably won't work if they're anything
other than simply resource.Resource, because ProxyMap uses
.getStaticEntity to traverse the resource tree.

This also includes the fix for http://twistedmatrix.com/bugs/issue1117
"twisted.web.proxy.ReverseProxyResource incorrectly sends host header
with no port," but in a slightly different form.

Deficiencies:

It does not support anything other than plain HTTP for either side of
the reverse proxy.

At foom's request (if I understood it correctly), this is written as a
bunch of subclasses rather than simply a patch.  Consequently a lot of
it consists of calls to super.

There are relatively thorough tests for ProxyMap, hostport, and
URLPathWithRelpath, but not with_explicit_port, ReverseProxyResource,
ProxyClientFactory, or ProxyClient.  None of these tests yet use trial
or even unittest; I have not yet learned how to write tests with
trial.

It will raise an exception trying to rewrite redirect URLs when
talking to a client that doesn't send a Host: header.

It does not support credentials in the redirect URLs.

Copyright 2005, CommerceNet.  By Kragen Sitaker.

"""
#'#"#'#"# appease Emacs's stupid quote matching

### to actually rewrite the location header, we need to intercept it;
# here we have subclasses of the relevant classes.

class ProxyClient(twisted.web.proxy.ProxyClient):
    def handleHeader(self, key, value):
        if key == 'location':
            value = self.proxymap.absoluteURLOf(value, self.host_header())
        return twisted.web.proxy.ProxyClient.handleHeader(self, key, value)
    def host_header(self):
        host = self.father.getHeader("host")
        assert host is not None  # XXX there are other alternatives...
        return host
    def __init__(self, command, rest, version, headers, data, father, proxymap):
        twisted.web.proxy.ProxyClient.__init__(self,
                                               command=command,
                                               rest=rest,
                                               version=version,
                                               headers=headers,
                                               data=data,
                                               father=father)
        self.proxymap = proxymap

class ProxyClientFactory(twisted.web.proxy.ProxyClientFactory):
    def __init__(self, command, rest, version, headers, data, father, proxymap):
        twisted.web.proxy.ProxyClientFactory.__init__(self,
                                                      command=command,
                                                      rest=rest,
                                                      version=version,
                                                      headers=headers,
                                                      data=data,
                                                      father=father)
        self.proxymap = proxymap
    def buildProtocol(self, addr):
        return ProxyClient(command=self.command,
                           rest=self.rest,
                           version=self.version,
                           headers=self.headers,
                           data=self.data,
                           father=self.father,
                           proxymap=self.proxymap)

def hostport(host, port, defaultport=80):
    if port == defaultport: return host
    return '%s:%d' % (host, port)

class ReverseProxyResource(twisted.web.proxy.ReverseProxyResource):
    clientFactory = ProxyClientFactory
    def __init__(self, host, port, path, proxymap):
        twisted.web.proxy.ReverseProxyResource.__init__(self, host, port, path)
        self.proxymap = proxymap
    def getChild(self, path, request):
        # XXX have to make sure we get this one instead of the other one
        return ReverseProxyResource(self.host, self.port, self.path+'/'+path,
                                    proxymap=self.proxymap)
    def render(self, request):
        # XXX too bad we had to copy and paste all this code due to
        # its poor factoring!

        # Copy 'headers' rather than modify it in place --- we may
        # need that 'Host:' header to correctly rewrite redirects
        # later on.
        headers = request.getAllHeaders().copy()
        headers['host'] = hostport(self.host, self.port)

        request.content.seek(0, 0)
        qs = urlparse.urlparse(request.uri)[4]
        if qs:
            rest = self.path + '?' + qs
        else:
            rest = self.path
        clientFactory = self.clientFactory(command=request.method,
                                           rest=rest, 
                                           version=request.clientproto, 
                                           headers=headers,
                                           data=request.content.read(),
                                           father=request,
                                           proxymap=self.proxymap)
        twisted.internet.reactor.connectTCP(self.host, self.port, clientFactory)
        return twisted.web.server.NOT_DONE_YET

### Proxy map objects.

def with_explicit_port(orig, default_port=80):
    assert '@' not in orig   # XXX we don't support credentials yet
    if ':' in orig: return orig
    else: return '%s:%d' % (orig, default_port)

class URLPathWithRelpath(twisted.python.urlpath.URLPath):
    def relativePathTo(self, other_absolute_url):
        """Path from me to absolute URL string 'other_absolute_url'.

        If 'child' is a descendant of mine, returns the intermediate path
        segments to get there; otherwise returns None.

        """
        c = twisted.python.urlpath.URLPath.fromString(other_absolute_url)
        assert self.scheme == 'http'
        if self.scheme != c.scheme: return None
        # XXX 80 is too specific, but I'm not supporting non-http
        # schemes yet (see assert above)
        if with_explicit_port(self.netloc) != with_explicit_port(c.netloc):
            return None
        bpath = self.pathList()
        if bpath[-1] == '': bpath = bpath[:-1]  # trailing slash
        if c.pathList()[:len(bpath)] == bpath:
            return urlparse.urlunsplit((None, None,
                                        '/'.join(c.pathList()[len(bpath):]),
                                        c.query, c.fragment))
        return None

def urlpath(urlstring):
    return URLPathWithRelpath(*urlparse.urlsplit(urlstring))

class ProxyMap:
    def __init__(self, urlmap): self.urlmap = urlmap
    #resourceType = twisted.web.proxy.ReverseProxyResource
    resourceType = ReverseProxyResource
    def createMappings(self, root):
        """Create ReverseProxyResources to establish this mapping.

        Walks the resource tree to find the place to insert each
        ReverseProxyResource, then putChild()s it there.

        """
        for k, v in self.urlmap.items():
            assert k.startswith('/')
            path = k.split('/')[1:]
            node = root
            for segment in path[:-1]:
                node = node.getStaticEntity(segment)
                assert node is not None
            scheme, netloc, lpath, query, frag = urlparse.urlsplit(v)
            assert scheme == 'http'  # ReverseProxyResource only does http
            assert query == ''    # how would you handle a query?
            assert frag == ''     # and a fragment would obviously be nonsense
            (host, port) = with_explicit_port(netloc).split(':')
            node.putChild(path[-1], self.resourceType(host, int(port), lpath,
                                                      proxymap=self))
    def reverseMap(self, url):
        """Finds the local URL path at which some absolute URL is mapped.

        For rewriting HTTP "Location:" headers in redirects.

        """
        for k, v in self.urlmap.items():
            path = urlpath(v).relativePathTo(url)
            if path is not None:
                if path == '': return k
                if k.endswith('/'): return k + path
                return k + '/' + path
        return None  # normally we return a path, not an absolute URL

    def absoluteURLOf(self, mappable_url, host_header):
        """Remaps an URL into my URL space if possible.

        host_header is the hostname and possibly port by which this
        server is known.

        Note that this doesn't have https support, even on the front
        end, yet.  That would probably involve making host_header
        become a URL.
        """
        path = self.reverseMap(mappable_url)
        if path is None: return mappable_url
        else: return 'http://%s%s' % (host_header, path)

def ok(a, b): assert a == b, (a, b)
def test_hostport():
    ok(hostport('wibble', 80), 'wibble')
    ok(hostport('wibble', 8080), 'wibble:8080')

def test_relative_paths():
    mapurl = urlpath('http://localhost/foo/bar').relativePathTo
    ok(mapurl('http://localhost/foo/bar/baz'), 'baz')
    ok(mapurl('http://localhost/foo/bar/buz'), 'buz')
    ok(mapurl('http://localhost/foo/bar/baz/buz'), 'baz/buz')
    ok(mapurl('http://localhost/foo/bar'), '')
    ok(mapurl('http://localhost/foo/bar/'), '')
    ok(mapurl('http://somewhereelse/foo/bar/baz'), None)
    ok(mapurl('http://localhost:8080/foo/bar/baz'), None)
    ok(mapurl('http://localhost/foo/barbaz'), None)

    # with trailing slash
    mapurl2 = urlpath('http://localhost/bar/').relativePathTo
    ok(mapurl2('http://localhost/foo/bar'), None)
    ok(mapurl2('http://localhost/bar/'), '')
    ok(mapurl2('http://localhost/bar'), '')  # not sure about this one
    ok(mapurl2('http://localhost/bar/bligz'), 'bligz')
    ok(mapurl2('http://localhost/barbligz'), None)

    # Usage scenario in reverse proxy includes construction of 'host'
    # header from the host and port, so we can't ensure that the
    # default port will be present or omitted exactly as in the mapped
    # URL.  So:

    # default port
    ok(urlpath('http://www:80/x').relativePathTo('http://www/x'), '')
    ok(urlpath('http://www:80/x').relativePathTo('http://www:80/x'), '')
    ok(urlpath('http://www/x').relativePathTo('http://www:80/x'), '')

    # nondefault port
    ok(urlpath('http://www:8080/x').relativePathTo('http://www/x'), None)
    ok(urlpath('http://www:8080/x').relativePathTo('http://www:8080/x'), '')
    ok(urlpath('http://www/x').relativePathTo('http://www:8080/x'), None)

    # Since that means we have to actually parse URLs, make sure we're
    # paying attention to the scheme:
    ok(urlpath('http://www/x').relativePathTo('ftp://www/x'), None)
    ok(urlpath('http://www/x').relativePathTo('https://www/x'), None)

    # and not discarding the query:
    gbase = urlpath('http://google.com/x')
    ok(gbase.relativePathTo('http://google.com/x/y?z'), 'y?z')
    # or fragment:
    ok(gbase.relativePathTo('http://google.com/x/y#2'), 'y#2')

def test_proxymap():
    p = ProxyMap({'/foo': 'http://localhost:8000/f00',
                  '/slash': 'http://localhost:8100/slash/',
                  '/slush/': 'http://localhost:8100/slush',
                  '/bar': 'http://localhost/b4r',
                  '/baz/quux': 'http://localhost:8000/quux'})

    ok(p.reverseMap('http://localhost:8000/f00'), '/foo')
    ok(p.reverseMap('http://localhost:8000/f00/bar'), '/foo/bar')
    ok(p.reverseMap('http://localhost:8000/quux/snorf'), '/baz/quux/snorf')
    ok(p.reverseMap('http://localhost/b4r/bie'), '/bar/bie')

    # on non-match, we return None (not the original url)
    ok(p.reverseMap('http://www.google.com/'), None)
    ok(p.reverseMap('http://localhost:8000/uhoh'), None)
    # starts with "/bar"...
    ok(p.reverseMap('http://localhost/barbarian'), None)

    # What to do about trailing slashes?

    # For now, since I can't figure out what the right thing is, I
    # won't care.

    #ok(p.reverseMap('http://localhost:8100/slush/'), '/slush/')
    #ok(p.reverseMap('http://localhost:8100/slush'),  '/slush/')
    #ok(p.reverseMap('http://localhost:8100/slash/'), '/slash/')
    #ok(p.reverseMap('http://localhost:8100/slash'),  '/slash')

    # but no double slash:
    ok(p.reverseMap('http://localhost:8100/slash/mush'), '/slash/mush')
    ok(p.reverseMap('http://localhost:8100/slush/mush'), '/slush/mush')

    # absolute URL
    ok(p.absoluteURLOf('http://localhost:8000/f00', 'wurble:9019'),
       'http://wurble:9019/foo')
    ok(p.absoluteURLOf('http://localhost/b4r/bie', 'ken.example.org'),
       'http://ken.example.org/bar/bie')
    ok(p.absoluteURLOf('http://google.com/search?q=guacamole', 'irrelevant'),
       'http://google.com/search?q=guacamole')
    

    ## creating mappings to set up a reverse-proxy site
    import twisted.web.resource
    r = twisted.web.resource.Resource()
    # haven't yet figured out what it should do about creating
    # intermediate nodes, so for now we require that the already exist
    r.putChild('slush', twisted.web.resource.Resource())
    r.putChild('baz', twisted.web.resource.Resource())
    p.createMappings(r)

    # contents of a ReverseProxyResource
    rpr = lambda res: (res.host, res.port, res.path)

    ok(rpr(r.getStaticEntity("foo")), ('localhost', 8000, '/f00'))
    ok(rpr(r.getStaticEntity("slash")), ('localhost', 8100, '/slash/'))
    ok(rpr(r.getStaticEntity("slush").getStaticEntity("")),
       ('localhost', 8100, '/slush'))
    ok(rpr(r.getStaticEntity("bar")), ('localhost', 80, '/b4r'))
    ok(rpr(r.getStaticEntity('baz').getStaticEntity('quux')),
       ('localhost', 8000, '/quux'))

def test():
    test_hostport()
    test_relative_paths()
    test_proxymap()

# When my machine is at 600MHz, this module takes only 6-10ms to
# reload with this in, so I feel justified at running it on every
# reload, even without it, reloading would take less than 1ms.
test()
