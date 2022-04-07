import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from twisted.internet import asyncioreactor
asyncioreactor.install()

import os
import shutil

from twisted.cred import checkers, credentials, portal
from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator, Protocol
from twisted.protocols.ftp import FTPClient, FTPRealm, FTPFactory, ConnectionLost
from twisted.trial import unittest


class BaseFTPTestCase(unittest.TestCase):
    username = "user"
    password = "passwd"

    def setUp(self):
        self.directory = self.mktemp()
        os.mkdir(self.directory)
        realm = FTPRealm(anonymousRoot=self.directory, userHome=self.directory)
        p = portal.Portal(realm)
        users_checker = checkers.InMemoryUsernamePasswordDatabaseDontUse()
        users_checker.addUser(self.username, self.password)
        p.registerChecker(users_checker, credentials.IUsernamePassword)
        self.factory = FTPFactory(portal=p)
        self.port = reactor.listenTCP(0, self.factory, interface="127.0.0.1")
        self.portNum = self.port.getHost().port
        self.addCleanup(self.port.stopListening)

    def tearDown(self):
        shutil.rmtree(self.directory)

    def test_invalid_credentials(self):
        user = self.username
        password = 'invalid'
        creator = ClientCreator(reactor, FTPClient, user, password, passive=1)
        deferred = creator.connectTCP('127.0.0.1', self.portNum)
        deferred.addCallback(self.gotClient)

        def _clean(data):
            self.client.transport.loseConnection()
            return data

        def _test(r):
            self.assertEqual(r.type, ConnectionLost)

        deferred.addBoth(_clean)
        deferred.addErrback(_test)
        return deferred

    def gotClient(self, client):
        self.client = client
        protocol = Protocol()
        return client.retrieveFile('file.txt', protocol)
