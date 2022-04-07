from cStringIO import StringIO
import time

from twisted.internet import reactor, task
from twisted.web import server, resource, client, http_headers


def main(argv):
    site = server.Site(resource.Resource())
    port = reactor.listenTCP(27500, site)

    agent = client.Agent(reactor)
    bodyProducer = client.FileBodyProducer(StringIO('[1,2,3]'))
    req = agent.request(
        'POST', 'http://127.0.0.1:27500/',
        http_headers.Headers({'Content-Type': ['application/json']}),
        bodyProducer)

    reactor.callLater(0.05, req.cancel)
    reactor.callLater(0, time.sleep, 0.1)

    return req

if __name__ == '__main__':
    task.react(main)
