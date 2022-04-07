from twisted.internet import defer
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.internet.ssl import CertificateOptions
from twisted.internet.task import react
from twisted.web.client import (
    HTTP11ClientProtocol, Request, readBody)
from twisted.web.http_headers import Headers

PROXY_HOST = '127.0.0.1'
PROXY_PORT = 8080
DEST_HOST = 'twistedmatrix.com'
DEST_METHOD = 'GET'
DEST_PORT = 443
DEST_PATH = '/'

def make_proxy_request():
    connect_dest = '{}:{}'.format(DEST_HOST, DEST_PORT)
    proxy_headers = Headers({'host': [connect_dest]})
    proxy_request = Request(
        'CONNECT', connect_dest, proxy_headers, None, persistent=True)

    return proxy_request

def make_real_request():
    real_headers = Headers({'host': [DEST_HOST]})
    real_request = Request(
        'GET', DEST_PATH, real_headers, None)

    return real_request

@defer.inlineCallbacks
def do_request(reactor):
    endpoint = TCP4ClientEndpoint(reactor, PROXY_HOST, PROXY_PORT)
    proto = HTTP11ClientProtocol()
    yield connectProtocol(endpoint, proto)

    proxy_request = make_proxy_request()
    response = yield proto.request(proxy_request)
    if response.code < 200 or response.code >= 300:
        raise Exception('Proxy Request Failed: {}'.format(response.code))

    proto.transport.startTLS(CertificateOptions())

    real_request = make_real_request()
    response = yield proto.request(real_request)
    body = yield readBody(response)

    print body

if __name__ == '__main__':
    react(do_request)
