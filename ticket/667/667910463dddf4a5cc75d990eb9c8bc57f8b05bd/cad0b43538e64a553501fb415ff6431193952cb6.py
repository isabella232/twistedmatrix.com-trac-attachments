from twisted.internet import iocpreactor
iocpreactor.install()

import os
import unittest

from twisted.internet import reactor, protocol, defer
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.iocpreactor.const import ERROR_IO_PENDING
from twisted.internet.iocpreactor.tcp import Connection
from twisted.trial.unittest import TestCase


class BufferServerProtocol(protocol.Protocol):
    '''
    Stores all received data for verification by a test.
    '''

    def connectionMade(self):
        self.receivedBytes = []
        self.count = 0
        self.targetCount = None
        self.d = None

    def dataReceived(self, data):
        self.receivedBytes.append(data)
        self.count += len(data)
        if self.targetCount and self.count >= self.targetCount:
            self.targetCount = None
            self.d.callback(''.join(self.receivedBytes))

    def readData(self, count):
        assert self.d is None, 'readData() can only be called once'
        self.targetCount = count
        self.d = defer.Deferred()
        return self.d


class URandomClientProtocol(protocol.Protocol):
    '''
    Sends random bytes at request, and stores sent bytes for verification.
    '''

    def connectionMade(self):
        self.dataSent = []

    def sendData(self, byteCount):
        data = os.urandom(byteCount)
        self.dataSent.append(data)
        self.transport.write(data)

    def getSentData(self):
        return ''.join(self.dataSent)


class DataDuplicationTest(TestCase):
    def setUp(self):
        self.patch(Connection, 'writeToHandle', self.createMockWriteToHandle())

    def createMockWriteToHandle(self):
        '''
        Mock out Connection.writeToHandle so that we know when ERROR_IO_PENDING
        is returned from Windows.
        '''
        original_writeToHandle = Connection.writeToHandle
        def mock_writeToHandle(conn, buff, evt):
            rc, bytes = original_writeToHandle(conn, buff, evt)
            if rc == ERROR_IO_PENDING:
                self.bufferIsFull = True
            return rc, bytes
        return mock_writeToHandle

    def startServer(self):
        p = BufferServerProtocol()
        factory = protocol.ServerFactory()
        factory.buildProtocol = lambda addr: p
        p.port = reactor.listenTCP(0, factory, interface='127.0.0.1')
        return p

    def connectClient(self, port):
        endpoint = TCP4ClientEndpoint(
            reactor, '127.0.0.1', port.getHost().port)
        clientfactory = protocol.ClientFactory()
        clientfactory.protocol = URandomClientProtocol
        return endpoint.connect(clientfactory)

    def yieldToMainLoop(self):
        d = defer.Deferred()
        reactor.callLater(0, d.callback, None)
        return d

    @defer.inlineCallbacks
    def test_noDataDuplicationWhenWriteBufferIsFull(self):
        self.bufferIsFull = False

        server = self.startServer()
        client = yield self.connectClient(server.port)

        # Pause reading so that the write buffer fills up
        server.transport.pauseProducing()

        i = 0
        # Send lots of data to fill the write buffer
        while not self.bufferIsFull:
            client.sendData(100000)
            yield self.yieldToMainLoop()
            while client.transport.dataBuffer and not self.bufferIsFull:
                yield self.yieldToMainLoop()
            i += 1
            if i >= 100:
                assert False, 'could not fill buffer'

        # Send more data to trigger bug #3525
        client.sendData(10)
        sentBytes = client.getSentData()

        # Read the bytes and verify that they're correct
        server.transport.resumeProducing()
        receivedBytes = yield server.readData(len(sentBytes))

        client.transport.loseConnection()
        server.port.stopListening()
        assert sentBytes == receivedBytes


if __name__ == '__main__':
    unittest.main()
