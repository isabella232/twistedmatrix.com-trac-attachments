import sys
import time
import md5
if "freebsd" in sys.platform:
    from twisted.internet import kqreactor
    kqreactor.install()
elif "linux" in sys.platform:
    from twisted.internet import epollreactor
    epollreactor.install()
from twisted.internet import protocol
from twisted.internet import reactor
#required for using threads with the Reactor
from twisted.python import threadable
threadable.init()
class Protocol(protocol.Protocol):
    """ClientProtocol"""
    data = ""
    maxConnections = 5000
    def connectionMade(self):
        self.factory.countConnections += 1
        if self.factory.countConnections > self.maxConnections:
            """Too many connections, try later"""
            self.transport.loseConnection()
    def connectionLost(self, reason):
        self.factory.countConnections -= 1
        self.transport.loseConnection()
    def dataReceived(self, data):
        """As soon as any data is received, write it back."""
        self.data = self.data + data
        self.parseCommand()
    def parseCommand(self):
        """Must be overridden"""
        self.handleCommand()
    def handleCommand(self):
        """Must be overridden"""
        response = ""
        self.sendResponse(response)
    def sendResponse(self, response):
        """Must be overridden"""
        msg = self.data
        print msg
        self.transport.write(msg)
class ClientFactory(protocol.ClientFactory):
    """ClientFactory"""
    countConnections = 0
    clients = {}
    def __init__(self, pr = Protocol):
        self.protocol = pr
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed:", reason
class ReconnectingClientFactory(protocol.ReconnectingClientFactory):
    """ReconnectingClientFactory"""
    def __init__(self, pr = Protocol):
        self.protocol = pr
        self.initialDelay = 1
        self.delay = self.initialDelay
        self.maxDelay = 60
        self.factor = 1
    def clientConnectionLost(self, connector, reason):
        print "Lost connection. Reason:", reason
        time.sleep(self.delay)
        self.delay *=  self.factor
        if self.delay > self.maxDelay:
            self.delay = self.maxDelay
        connector.connect()
    def clientConnectionFailed(self, connector, reason):
        print "Connection failed. Reason:", reason
        time.sleep(self.delay)
        self.delay *=  self.factor
        if self.delay > self.maxDelay:
            self.delay = self.maxDelay
        connector.connect()
class Server(object):
    """Server"""
    protocols = {}
    def __init__(self, listeningPorts = {}, connectingPorts = {}):
        self.listeningPorts = listeningPorts
        self.connectingPorts = connectingPorts
        self.factories = {}
        # Множество слушающих портов
        for item in self.listeningPorts.iteritems():
            protocolID = item[0]
            protocol = self.protocols[protocolID]
            factory = ClientFactory(protocol)
            self.factories[protocolID] = factory
        # Множество коннектящихся портов
        for item in self.connectingPorts.iteritems():
            protocolID = item[0]
            protocol = self.protocols[protocolID]
            factory = ReconnectingClientFactory(protocol)
            self.factories[protocolID] = factory
    def __del__(self):
        pass
    def start(self):
        """Start the server"""
        self.__reactor = reactor
        self.__listener = {}
        self.__connector = {}
        for item in self.listeningPorts.iteritems():
            protocolID = item[0]
            protocol = self.protocols[protocolID]
            host, port = item[1]
            self.__listener[protocolID] = self.__reactor.listenTCP(port, self.factories[protocolID])
        for item in self.connectingPorts.iteritems():
            protocolID = item[0]
            protocol = self.protocols[protocolID]
            host, port = item[1]
            self.__connector[protocolID] = self.__reactor.connectTCP(host, port, self.factories[protocolID],timeout=0.5)
        self.__reactor.run(installSignalHandlers=0)
    def stop(self):
        """Correct way to stop the server"""
        self.__reactor.stop()
    def crash(self):
        """Crash the server. Data may be lost"""
        for protocolID in self.listeningPorts.iterkeys():
            self.__listener[protocolID].connectionLost("")
        for protocolID in self.connectingPorts.iterkeys():
            self.__listener[protocolID].connectionLost("")
        self.__reactor.crash()
    def cold_restart(self):
        """May be overridden"""
    def soft_restart(self):
        """May be overridden"""
    def hard_restart(self):
        """May be overridden"""
    def status(self):
        """Server status (running or not)"""
        return self.__reactor.running
