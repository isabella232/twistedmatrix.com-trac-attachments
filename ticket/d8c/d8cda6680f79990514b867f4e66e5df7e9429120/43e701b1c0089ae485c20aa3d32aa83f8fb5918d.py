#!/usr/bin/python

import httpbin, requests

from twisted.internet import reactor, threads, defer, endpoints
from twisted.web.wsgi import WSGIResource
from twisted.web.server import Site

def sleep_a_bit():
	d = defer.Deferred()
	reactor.callLater(10.0, d.callback, None)
	return d

def failing_get(url):
	try:
		requests.get(url, timeout = (1.0, 0.00001))
	except requests.exceptions.ReadTimeout:
		pass

@defer.inlineCallbacks
def startup():
	try:
		resource = WSGIResource(reactor, reactor.getThreadPool(), httpbin.app)
		site = Site(resource)
		port = yield endpoints.TCP4ServerEndpoint(reactor, 8888).listen(site)

		for i in xrange(10):
			threads.deferToThread(failing_get, 'http://127.0.0.1:8888/delay/1')

		yield sleep_a_bit()

		yield port.stopListening()
	except Exception as e:
		print e
	finally:
		reactor.stop()

reactor.callWhenRunning(startup)
reactor.run()
