from twisted.trial import unittest
from twisted.enterprise import adbapi

class sampleCase(unittest.TestCase):

    def test_sql(self):
        dbpool = adbapi.ConnectionPool("MySQLdb",host="localhost",
                                       user='sample',passwd='sample',db='sampledb')
        d = dbpool.runQuery('select * from yourtable')
        return d
