from twisted.enterprise import adbapi
from twisted.trial import unittest

from twisted.internet.defer import inlineCallbacks, returnValue

import sqlite3

class TestReuseErrConnections(unittest.TestCase):
    """
    I test that you can reuse Connections/Transactions from a ConnectionPool if there
    was previously an error running a query with that Connection/Transaction.
    """

    def test_queries3(self):
        """
        I test that running a bad query will not polute that Connection for future
        queries.

        In this test, we start with a bad query, then the 3rd query after that (from cp_min)
        will reuse the bad Connection left by the bad query.
        """
        pool = adbapi.ConnectionPool('sqlite3', self.mktemp(), check_same_thread=False, cp_min=3)
        d = pool.runQuery('drop table foo')
        def eb1(res):
            q1 = pool.runQuery('create table foo (name text)')
            def doq2(res):
                q2 = pool.runQuery("insert into foo (name) values ('bar');")
                def doq3(res):
                    q3 = pool.runQuery("insert into foo (name) values ('bar');")
                    return q3
                return q2.addCallback(doq3)
            return q1.addCallback(doq2)
        d.addErrback(eb1)
        def f(r):
            print 'final output', r
            return r
        return d

    @inlineCallbacks
    def test_inlinecallbacks(self):
        """
        I test the same thing as above, only with inlineCallbacks
        """
        fname = self.mktemp()
        pool = adbapi.ConnectionPool('sqlite3', fname, check_same_thread=False, cp_min=3, cp_max=3)
        try:
            _ = yield pool.runQuery('drop table foo')
        except Exception, e:
            pass
        q1 = yield pool.runQuery('create table foo (name text)')
        q2 = yield pool.runQuery("insert into foo (name) values ('bar');")
        q3 = yield pool.runQuery("insert into foo (name) values ('bar');")

