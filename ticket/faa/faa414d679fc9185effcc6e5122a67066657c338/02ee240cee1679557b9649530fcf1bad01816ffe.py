#!/usr/bin/env python

import tempfile, os
from twisted.trial import unittest
from twisted.web import server, resource, client, vhost, proxy, static
from twisted.internet import reactor, defer

EXPECTED_HTML = "<html>Hello, World!</html>\n"
INTERNAL_HOSTNAME = "localhost"
INTERNAL_PORT = 8538
INTERNAL_URL = "http://%s:%d/" % (INTERNAL_HOSTNAME, INTERNAL_PORT)
EXTERNAL_HOSTNAME = "127.0.0.1"
EXTERNAL_PORT = 8001
EXTERNAL_URL = "http://%s:%d/" % (EXTERNAL_HOSTNAME, EXTERNAL_PORT)


class Simple(resource.Resource):
    def getChild(self, name, request):
        if name == '':
            return self
        return Resource.getChild(self, name, request) 

    def render_GET(self, request):
        return EXPECTED_HTML

class ReverseProxyTest(unittest.TestCase):

    def setUp(self):
        self.p1 = None
        self.p2 = None

        # Create a temporary doc root directory
        self.tempDocRoot = tempfile.mkdtemp()
        self.indexFilename = self.tempDocRoot + "/index.html"
        indexFile = file(self.indexFilename, 'w')
        indexFile.write(EXPECTED_HTML)
        indexFile.close()

        self.testFilename = self.tempDocRoot + "/test.html"
        testFile = file(self.testFilename, 'w')
        testFile.write(EXPECTED_HTML)
        testFile.close()

    def tearDown(self):
        # Remove the temporary doc root directory
        os.remove(self.indexFilename)
        os.remove(self.testFilename)
        os.rmdir(self.tempDocRoot)

        dl = []
        if self.p1:
            dl.append(self.p1.stopListening())
        if self.p2:
            dl.append(self.p2.stopListening())

        return defer.gatherResults(dl)

    def _startExternalServer(self):
        vhostName = EXTERNAL_HOSTNAME
        reverseProxy = proxy.ReverseProxyResource(INTERNAL_HOSTNAME, 
                                                  INTERNAL_PORT,
                                          '/vhost.rpy/http/'+vhostName+'/')
        root = vhost.NameVirtualHost()
        root.addHost(vhostName, reverseProxy)
        site = server.Site(root)
        self.p1 = reactor.listenTCP(EXTERNAL_PORT, site)

    def _startInternalServerWithDynamicResource(self):
        root = Simple()
        root.putChild('test.html', Simple())
        self._startInternalServer(root)

    def _startInternalServerWithStaticFile(self):
        self._startInternalServer( static.File( self.tempDocRoot ) )

    def _startInternalServer(self, root):
        root.putChild('vhost.rpy', vhost.VHostMonsterResource())
        site = server.Site(root)
        self.p2 = reactor.listenTCP(INTERNAL_PORT, site)

    def testInternalServerWithDynamicResource(self):
        self._startInternalServerWithDynamicResource()
        d = client.getPage(INTERNAL_URL)
        d.addCallback(self._verifyInternalServerResponse)
        return d

    def testInternalServerWithStaticFile(self):
        self._startInternalServerWithStaticFile()
        d = client.getPage(INTERNAL_URL)
        d.addCallback(self._verifyInternalServerResponse)
        return d

    def testReverseProxyServerWithInternalDynamicIndexResource(self):
        self._startInternalServerWithDynamicResource()
        self._startExternalServer()
        d = client.getPage(EXTERNAL_URL)
        d.addCallback(self._verifyInternalServerResponse)
        return d

    def testReverseProxyServerWithInternalStaticIndexFile(self):
        self._startInternalServerWithStaticFile()
        self._startExternalServer()
        d = client.getPage(EXTERNAL_URL)
        d.addCallback(self._verifyInternalServerResponse)
        return d

    def _verifyInternalServerResponse(self, res):
        self.failUnlessEqual(res, EXPECTED_HTML)
        #print res

    def testReverseProxyServerWithInternalDynamicResource(self):
        self._startInternalServerWithDynamicResource()
        self._startExternalServer()
        d = client.getPage(EXTERNAL_URL+"/test.html")
        d.addCallback(self._verifyInternalServerResponse)
        return d

    def testReverseProxyServerWithInternalStaticFile(self):
        self._startInternalServerWithStaticFile()
        self._startExternalServer()
        d = client.getPage(EXTERNAL_URL+"/test.html")
        d.addCallback(self._verifyInternalServerResponse)
        return d

