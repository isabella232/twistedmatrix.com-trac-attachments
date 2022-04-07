import sys
from traceback import print_exc
from twisted.internet.defer import inlineCallbacks, returnValue, maybeDeferred
from twisted.internet.task import react
from twisted.python.failure import Failure

def real_bad():
    return 1 / 0

@inlineCallbacks
def something_failing():
    yield maybeDeferred(real_bad)

@inlineCallbacks
def method(arg, kw=None):
    try:
        yield something_failing()
    except Exception as e:
        f = Failure()
        # traceback goes to 3 lines up, not into real_bad ...
        print("STDLIB\n")
        print_exc()

        # twisted figures out the 'real' stack-trace
        print("\nTWISTED\n")
        f.printTraceback(file=sys.stdout)

method('foo')
