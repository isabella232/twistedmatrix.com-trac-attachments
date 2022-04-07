try:
    import copy_reg as _compat_copy_reg
except ImportError:
    import copyreg as _compat_copy_reg

import pickle
import platform
import types

try:
    import cPickle
except ImportError:
    cPickle = None

_PYPY = platform.python_implementation() == 'PyPy'


def _ignored():
    """Satisfy pickle"""


callCount = 0

expectedCallCount = 2 if _PYPY else 1


def customPickleFunction(f):
    global callCount
    callCount += 1
    return (_ignored, tuple('A'))


_compat_copy_reg.pickle(types.FunctionType, customPickleFunction)


def testSubject():
    """Try to serialize me"""

pickle.dumps(testSubject)
assert not callCount, ("pickle.dumps(testSubject) should not"
                       " have called customPickleFunction")

if cPickle:
    cPickle.dumps(testSubject)
    assert not callCount, ("cPickle.dumps(testSubject) should not"
                           " have called customPickleFunction")
try:
    pickle.dumps(lambda: None)
except pickle.PicklingError:
    pass
else:
    if not _PYPY:
        assert False, ('pickle.dumps(lambda: None) should have'
                       ' raised PicklingError on non-PyPy interpreters.')

if cPickle:
    cPickle.dumps(lambda: None)
    assert callCount == expectedCallCount, (
        "cPickle.dumps(lambda: None) should have"
        " called customPickleFunction")
