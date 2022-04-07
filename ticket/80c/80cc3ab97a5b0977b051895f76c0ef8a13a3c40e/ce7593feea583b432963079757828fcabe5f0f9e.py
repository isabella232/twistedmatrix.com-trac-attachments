def queryAll():
    return conn.runQuery("SELECT * FROM directory")

def printAll(result):
    print result
    reactor.stop()

if __name__ == '__main__':
    from twisted.internet import reactor
    from twisted.enterprise import adbapi
    
    conn = adbapi.ConnectionPool('sqlite3', 'directory.sqlite', check_same_thread=False)
    dbdef =  queryAll()
    dbdef.addCallback(printAll)
    
    reactor.run()
