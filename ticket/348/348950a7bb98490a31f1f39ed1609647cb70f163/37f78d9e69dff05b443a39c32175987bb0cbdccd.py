from twisted.python.filepath import FilePath
from twisted.logger import Logger, textFileLogObserver, globalLogPublisher, globalLogBeginner
from twisted.internet.endpoints import SSL4ServerEndpoint
from twisted.internet.ssl import PrivateCertificate, Certificate
from twisted.internet.defer import Deferred
from twisted.internet.task import react
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
import codecs
import sqlite3
import os


import sys
globalLogBeginner.beginLoggingTo([textFileLogObserver(sys.stdout)])
loggy = Logger()

class Ex_Factory(Factory):
    def __init__(self, loggy):
        self.loggy = loggy
    def buildProtocol(self, addr):
        return Ex_Protocol(self.loggy)
class Ex_Protocol(LineReceiver):
    def dataReceived(self,data):
        self.loggy.info('mmm')
    def connectionMade(self):
        self.sendLine(b'hello')
        self.loggy.info('ConMade')
    def __init__(self, loggy):
        self.loggy = loggy
        self.loggy.info('Works')

    def lineReceived(self, data):
        self.loggy.info('I am not called! But why?')

def main(reactor):
    #Set up a SSL-Endpoint
    pemBytes = FilePath(b"private.pem").getContent()
    certificateAuthority = Certificate.loadPEM(pemBytes)
    myCertificate = PrivateCertificate.loadPEM(pemBytes)
    serverEndpoint = SSL4ServerEndpoint(
        reactor, 1234, myCertificate.options(certificateAuthority)
    )
    serverEndpoint.listen(Ex_Factory(loggy))
    return Deferred()
react(main, [])