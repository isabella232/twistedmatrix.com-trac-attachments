from twisted.web import server, static, proxy
from twisted.python import filepath
from twisted.application import service, strports

import tempfile

tempdir = filepath.FilePath(tempfile.mkdtemp())
tempdir.child('build').createDirectory()

frontend = server.Site(proxy.ReverseProxyResource('localhost', 8090, ''))
backend = server.Site(static.File(tempdir.path))

application = service.Application('repro for https://tm.tl/6478')

strports.service('tcp:8090', backend).setServiceParent(application)
strports.service('tcp:8080', frontend).setServiceParent(application)
