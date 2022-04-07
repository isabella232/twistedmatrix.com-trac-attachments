from twisted.internet.cdefer import Deferred
from twisted.python import failure

def cb1(res):
    raise ValueError
    return res

def eb1(res):
    return res

def eb2(res):
    return None


def main():
    for w in xrange(100000):
        d = Deferred()
        d.addCallback(cb1).addErrback(eb1).addBoth(eb2)
        d.callback("testData")

if __name__=='__main__':
    main()
