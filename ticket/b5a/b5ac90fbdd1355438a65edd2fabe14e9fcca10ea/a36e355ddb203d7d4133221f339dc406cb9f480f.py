from twisted.logger import globalLogPublisher, Logger, formatEvent
from twisted.logger._flatten import flattenEvent
from twisted.internet import reactor

log = Logger('test')

def test():
    log.info('test {var}', var='data') # ok
    log.info('begin {var} end', var='data') # format error


def observer(event):
    flattenEvent(event)
    print formatEvent(event)

globalLogPublisher.addObserver(observer)
reactor.callWhenRunning(test)
reactor.run()
