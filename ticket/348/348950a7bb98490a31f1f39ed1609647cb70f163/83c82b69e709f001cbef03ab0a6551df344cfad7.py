dir="/working_dir"
certname="private.pem"

from twisted.python.filepath import FilePath
from twisted.internet.endpoints import SSL4ClientEndpoint
from twisted.internet.ssl import (PrivateCertificate, Certificate, optionsForClientTLS)
from twisted.internet.defer import Deferred, inlineCallbacks
from twisted.internet.task import react
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
import os
class SendAnyData(LineReceiver):
    deferred = Deferred()
    def connectionMade(self):
        print('ConMade!')
        self.sendLine(b"START")
        self.transport.write(b"START\r\n")
    def connectionLost(self, reason):
        print('ConLost!')
        self.deferred.callback(None)
    def lineReceived(self, data):
        line = data.decode("UTF-8")

@inlineCallbacks
def main(reactor):
    def getServerandPort(i):
       return ("1.2.3.4",1234)
    pem = FilePath(b"Certificates/"+certname.encode("UTF-8")).getContent()
    caPem = FilePath(b"Certificates/ca-private-cert.pem").getContent()
    host, port = getServerandPort(0)

    clientEndpoint = SSL4ClientEndpoint(
            reactor, host, port,
            optionsForClientTLS(u"ABC", Certificate.loadPEM(caPem),
                                    PrivateCertificate.loadPEM(pem)),
    )
    factory = Factory.forProtocol(SendAnyData)
    proto = yield clientEndpoint.connect(factory)
    yield proto.deferred

os.chdir(dir)
react(main)