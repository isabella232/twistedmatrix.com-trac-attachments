from twisted.internet import defer, reactor

NO_OF_DEFERREDS = 332

def do_something(item, d):
    print item
    d.callback(item)

def start(items):
    if items:
        item = items[0]
        items = items[1:]
        d = defer.Deferred()
        reactor.callLater(0, lambda: do_something(item, d))
        d.addCallback(lambda _: start(items))
        return d
    reactor.stop()

def finished(_):
    print 'This should print after the numbers are done printing.'

if __name__ == '__main__':
    items = []
    for i in range(NO_OF_DEFERREDS):
        items.append(i)
    start(items).addCallback(finished)
    reactor.run()
