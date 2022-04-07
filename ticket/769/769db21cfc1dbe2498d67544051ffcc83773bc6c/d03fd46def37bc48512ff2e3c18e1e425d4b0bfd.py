#! /usr/bin/env python

from twisted.python.logfile import DailyLogFile
log = DailyLogFile('logfile.txt', '.')
f=open('logfile.txt', 'rb')
log.write('hello\n')
try:
    log.rotate()
except Exception, err:
    print 'error:', err
log.write('world')
