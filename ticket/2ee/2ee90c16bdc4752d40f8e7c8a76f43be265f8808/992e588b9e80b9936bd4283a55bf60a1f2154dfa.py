""" 
Example which triggers a re-connection issue in adbapi. 
Run with a mysql wait_timeout which is less than DELAY e.g. in /etc/my.ini:

[mysqld]
wait_timeout=2
"""

from twisted.enterprise import adbapi
from twisted.internet import reactor
from twisted.python import log
import sys

DELAY = 3

dbpool = adbapi.ConnectionPool(
        'MySQLdb', 
        db='mysql', 
        host='localhost', 
        user='root', 
        cp_noisy=True,
        cp_reconnect=True,
        cp_min=1,
        cp_max=1
)

def select_something():
    def p(r):
        log.msg("query returned", r)
        reactor.callLater(DELAY, select_something)
    return dbpool.runQuery("select 'something'").addCallback(p)

log.startLogging(sys.stdout)
reactor.callLater(DELAY, select_something)
reactor.run()
