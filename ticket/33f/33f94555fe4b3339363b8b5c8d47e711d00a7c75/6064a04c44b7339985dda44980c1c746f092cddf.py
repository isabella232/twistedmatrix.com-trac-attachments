import os
import gc
import objgraph
import sqlite3

from twisted.internet import reactor
from twisted.enterprise.adbapi import ConnectionPool

entries = 1000

def not_leaking():
    try:
        os.unlink('./test-nl.db3')
    except:
        pass

    connection = sqlite3.connect('./test-nl.db3')

    cursor = connection.cursor()
    cursor.execute('CREATE TABLE test_insert (id ROWID, value INTEGER);')

    query = 'INSERT INTO test_insert (value) VALUES (10)'

    gc.collect()
    objgraph.show_growth()

    print "Inserting %d rows (plain SQLite3)..." % entries
    for entry in range(entries):
        cursor.execute(query)

    connection.commit()

    gc.collect()
    objgraph.show_growth()

    cursor.close()
    connection.close()


def leaking():
    try:
        os.unlink('./test-l.db3')
    except:
        pass

    def create_table(cursor):
        cursor.execute('CREATE TABLE test_insert (id ROWID, value INTEGER);')

    query = 'INSERT INTO test_insert (value) VALUES (10)'
    def insert_entry(cursor):
        cursor.execute(query)

    def execute():
        pool = ConnectionPool('sqlite3', cp_min=1, cp_max=1, database='test-l.db3')
        pool.runInteraction(create_table)

        gc.collect()
        objgraph.show_growth()

        print "Inserting %d rows (Twisted)..." % entries
        last_d = None
        for entry in range(entries):
            last_d = pool.runInteraction(insert_entry)
            last_d.addCallback(lambda _: None)
        
        last_d.addCallback(pool.close)

    def terminate():
        reactor.stop()

    reactor.callLater(0, execute)
    reactor.callLater(1, terminate)

    reactor.run()

    gc.collect()
    objgraph.show_growth()
 

not_leaking()
leaking()
