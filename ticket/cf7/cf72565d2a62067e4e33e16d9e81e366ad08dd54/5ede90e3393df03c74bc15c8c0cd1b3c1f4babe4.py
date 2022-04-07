from twisted.internet.cdefer import Deferred
from twisted.python import failure

def cb1(res):
    return res

class FF(object):
    def __init__(self,f):
        self.f = f

def main():
    for w in xrange(100000):
        d = Deferred()
        d.addCallback(cb1)
        d.callback(FF(failure.Failure(ValueError())))

if __name__=='__main__':
    main()
