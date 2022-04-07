#!/usr/bin/env python

from twisted.web.server import Site, GzipEncoderFactory
from twisted.web.resource import EncodingResourceWrapper
from twisted.internet import reactor
from twisted.web.static import File, StaticProducer
import StringIO

#
# Serv a gzip compressed file containing repeating 'x' character
#
# Using:
#
#  run with 'python gzipbug.py'
#
#  direct your web-browser to http://localhost:8080/
#


class EncFile(File):
    isLeaf = True

    def __init__(self):
        # a hack to make File's calls to stat() work
        File.__init__(self, __file__)

    def openForReading(self):
        return StringIO.StringIO("x" * StaticProducer.bufferSize * 2)


resource = EncFile()
wrapped = EncodingResourceWrapper(resource, [GzipEncoderFactory()])
site = Site(wrapped)
reactor.listenTCP(8080, site)
reactor.run()
