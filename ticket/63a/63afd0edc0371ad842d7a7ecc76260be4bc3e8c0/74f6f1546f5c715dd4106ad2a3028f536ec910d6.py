from twisted.enterprise import adbapi
from twisted.trial import unittest

from twisted.internet.defer import inlineCallbacks, returnValue

import sqlite3

class TestReuseErrConnections(unittest.TestCase):
    """
    I test that you can reuse Connections/Transactions from a ConnectionPool if there
    was previously an error running a query with that Connection/Transaction.
    """

    createSql = 'create table foo (name text)'
    selectSql = 'select * from foo'
    insertSql = "insert into foo (name) values ('bar%(i)s')"
    updateSql = "update foo set name='wiggy%(i)s'"
    deleteSql = 'delete from foo'
    dropSql = 'drop table foo'
    badselectSql = 'select garbage'
    badinsertSql = 'insert into lskdjflskdjlfkjsdf'

    @inlineCallbacks    
    def doMany(self, manySql, createSql, pollution=None):
        """
        I test that running a bad SQL query, creating a table and running several inserts works -- that none
        of the queries fail.
        """
        fname = self.mktemp()
        pool = adbapi.ConnectionPool('sqlite3', fname, check_same_thread=False, cp_min=3, cp_max=3)
        
        # pollute a conn
        if pollution:
            try:
                _ = yield pool.runQuery(pollution)
            except Exception, e:
                pass
            
        # create a table
        failures = []
        numbers = [] 
        num = 10
        if createSql:
            _ = yield pool.runQuery(createSql)
        for i in xrange(num):
            try:
                a = yield pool.runQuery(manySql % {'i': i})
            except Exception, e:
                failures.append(e)
                numbers.append(i)
        if failures:
            self.fail('There were %d failures: %s\n%s' % (len(failures), numbers, '\n'.join(map(lambda x:repr(x), failures))))

    #-------------------------------------------------------------------------------
    # Control group
    #-------------------------------------------------------------------------------
    def test_no_pollute_insert(self):
        return self.doMany(self.insertSql, self.createSql)

    def test_no_pollute_select(self):
        return self.doMany(self.selectSql, self.createSql)

    def test_no_pollute_update(self):
        return self.doMany(self.updateSql, self.createSql)

    def test_no_pollute_delete(self):
        return self.doMany(self.deleteSql, self.createSql)

    #-------------------------------------------------------------------------------
    # bad drop
    #-------------------------------------------------------------------------------
    def test_drop_insert(self):
        return self.doMany(self.insertSql, self.createSql, self.dropSql)
    
    def test_drop_select(self):
        return self.doMany(self.selectSql, self.createSql, self.dropSql)
    
    #-------------------------------------------------------------------------------
    # bad select
    #-------------------------------------------------------------------------------
    def test_badselect_insert(self):
        return self.doMany(self.insertSql, self.createSql, self.badselectSql)
    
    def test_badselect_select(self):
        return self.doMany(self.selectSql, self.createSql, self.badselectSql)
    
    #-------------------------------------------------------------------------------
    # bad select that would otherwise be good
    #-------------------------------------------------------------------------------
    def test_sortabadselect_insert(self):
        return self.doMany(self.insertSql, self.createSql, self.selectSql)
    
    def test_sortabadselect_select(self):
        return self.doMany(self.selectSql, self.createSql, self.selectSql)
    
    #-------------------------------------------------------------------------------
    # bad insert
    #-------------------------------------------------------------------------------
    def test_badinsert_insert(self):
        return self.doMany(self.insertSql, self.createSql, self.badinsertSql)
    
    def test_badinsert_select(self):
        return self.doMany(self.selectSql, self.createSql, self.badinsertSql)
    
    #-------------------------------------------------------------------------------
    # bad insert that would otherwise be good
    #-------------------------------------------------------------------------------
    def test_sortabadinsert_insert(self):
        return self.doMany(self.insertSql, self.createSql, self.insertSql)
    
    def test_sortabadinsert_select(self):
        return self.doMany(self.selectSql, self.createSql, self.insertSql)
    










