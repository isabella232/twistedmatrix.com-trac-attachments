import gc, sys

from twisted.spread.pb import Root, PBServerFactory, PBClientFactory
from twisted.internet import reactor
from twisted.python.log import startLogging

def main():
    server = PBServerFactory(Root())
    server.noisy = False
    port = reactor.listenTCP(0, server)
    client = PBClientFactory()
    client.noisy = False
    def f():
        print len(gc.garbage), len(gc.get_objects())
        connector = reactor.connectTCP(port.getHost().host, port.getHost().port, client)
        d = client.getRootObject()
        def g(root):
            root.notifyOnDisconnect(lambda ign: reactor.callLater(0, f))
            connector.disconnect()
        d.addCallback(g)
    f()
    reactor.run()

if __name__ == '__main__':
    startLogging(sys.stdout)
    main()
