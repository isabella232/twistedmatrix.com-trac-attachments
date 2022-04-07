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

if 0:
    def logger(f):
        def _wrap(*args, **kwargs):
            ret = f(*args, **kwargs)
            log.msg('%r returned %r' % (f, ret))
            return ret

        _wrap.__name__ = f.__name__
        return _wrap



class TestCase(unittest.TestCase):
    @logger
    def test_Answer(self):
        return 49
