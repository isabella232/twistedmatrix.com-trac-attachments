#!/usr/bin/env python
from twisted.internet import ssl, reactor, task
from twisted.internet.protocol import Factory, Protocol
from twisted.python.log import startLogging
from sys import stdout
startLogging(stdout, False)

"""
mkdir keys
openssl genrsa -des3 -out server.key 4096
openssl req -new -key server.key -out server.csr
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
"""
class Echo(Protocol):
    def dataReceived(self, data):
        """As soon as any data is received, write it back."""
        self.transport.write(data)


def howMany():
    import instcount
    for (count, cls) in instcount.topClasses():
        if cls == 'TLSMemoryBIOProtocol':
            print count, cls

if __name__ == '__main__':
    task.LoopingCall(howMany).start(15)
    factory = Factory()
    factory.protocol = Echo
    reactor.listenSSL(8000, factory,
                      ssl.DefaultOpenSSLContextFactory(
            'server.pem', 'server.pem'))
    reactor.run()
