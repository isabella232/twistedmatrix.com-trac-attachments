from twisted.python import log
from twisted.trial import unittest



class logger(object):
    """A simple decorator implemented with a class.
    """

    def __init__(self, f):
        self.f = f
        self.__name__ = f.__name__

    def __call__(self, *args, **kwargs):
        ret = self.f(*args, **kwargs)
        log.msg('%r returned %r' % (f, ret))
        return ret

    def __get__(self, obj, objtype=None):
        if obj is None:
            print 'without obj'
            def _wrap(*args, **kwargs):
                ret = self.f(*args, **kwargs)
                log.msg('%r returned %r' % (self.f, ret))
                return ret
        else:
            print 'with obj'
            def _wrap(*args, **kwargs):
                ret = self.f(obj, *args, **kwargs)
                log.msg('%r returned %r' % (self.f, ret))
                return ret
            
        _wrap.__name__ = self.f.__name__
        return _wrap


class TestCase(unittest.TestCase):
    @logger
    def test_Answer(self):
        return 49


if __name__ == '__main__':
    class Test(object):
        @logger
        def test(self):
            return 49
        
    t = Test()
    print t.test()

