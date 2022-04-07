import os
import tempfile

from twisted.enterprise import adbapi

from twisted.trial import unittest

import MySQLdb
mysqlUsername = "idonot"
mysqlPassword = "exist"
mysqlHost = 'localhost'

class TestMySQL(unittest.TestCase):
    def setUp(self):
        self.dbpool = adbapi.ConnectionPool('MySQLdb', host=mysqlHost,
            user=mysqlUsername, passwd=mysqlPassword, db="test")
        #self.dbpool.start()

    def tearDown(self):
        #self.dbpool.close()
        pass

    def testInsert(self):
        self.dbpool.runQuery("SELECT hi")
        pass
