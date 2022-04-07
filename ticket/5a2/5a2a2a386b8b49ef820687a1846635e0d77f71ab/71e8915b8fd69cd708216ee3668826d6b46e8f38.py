from twisted.trial import unittest
from twisted.enterprise import adbapi

class TestConnectionPoolShutdown(unittest.TestCase):
    def testClosingAnUnstartdConnectionPoolDoesNotError(self):
        pool = adbapi.ConnectionPool('sqlite3')
        return pool.close()