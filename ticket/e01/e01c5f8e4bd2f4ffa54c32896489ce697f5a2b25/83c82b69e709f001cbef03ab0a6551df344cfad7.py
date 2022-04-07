from __future__ import print_function

from twisted.internet import reactor
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers

agent = Agent(reactor)

d = agent.request(
    b'GET',
    b'http://localhost:8080/',
    Headers({'User-Agent': ['Twisted Web Client Example']}),
    None)

def cbData(data):
    print("DATA:", repr(data))

def cbResponse(ignored):
    print('Response received')
    rd = readBody(ignored)
    rd.addCallback(cbData)
d.addCallback(cbResponse)

def cbShutdown(ignored):
    reactor.stop()
d.addBoth(cbShutdown)

reactor.run()
