# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import sys

from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import reactor

import time
import gtk


def get(i):
    print 'get', i
    # the task that does the work
    time.sleep(0.01)
    return i

def update(l, i):
    print 'update', i
    # the call that updates the UI
    l.set_text(str(i))
    time.sleep(0.01)


def blocking(l):
    for i in range(0, 1000):
        get(i)
        update(l, i)

def calllater(l):
    def later(l, i):
        get(i)
        update(l, i)

    for i in range(0, 1000):
        # 0.01 will definitely block the UI
        # 0.02 does too
        # 0.03 seems fine
        reactor.callLater(.025 * i, later, l, i)

def cooperator(l):
    def myiter(numbers):
        for n in numbers:
            get(n)
            update(l, n)
            yield None

    from twisted.internet import task
    c = task.Cooperator()
    c.cooperate(myiter(range(0, 1000)))

strategies = [
    "blocking",
    "calllater",
    "cooperator",
]

def main():

    w = gtk.Window()
    w.connect('destroy', lambda _: reactor.stop())
    w.set_default_size(320, 240)

    l = gtk.Label('start')

    w.add(l)

    w.show_all()



    try:
        strategy = sys.argv[1]
    except IndexError:
        strategy = 'cooperator'

    if not strategy in strategies:
        sys.stderr.write(
            'Please give a strategy from: %s\n' % ", ".join(strategies))
        sys.exit(1)

    reactor.callLater(1, globals()[strategy], l)

    reactor.run()

if __name__ == '__main__':
    main()
