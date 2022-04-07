import traceback
from decorator import decorator

from twisted.python.util import mergeFunctionMetadata

@decorator
def decorator_reverser(f, *args):
    return reverser(f)(*args)


def reverser(f):
    def g(*args):
        return f(*args[::-1])
    return mergeFunctionMetadata(f, g)


@reverser
def adder(a, b):
    print 'adding', a, 'and', b
    return a + b

@decorator_reverser
def decorator_adder(a, b):
    print 'adding', a, 'and', b
    return a + b


import inspect

print inspect.getargspec(decorator_reverser)
try:
    print inspect.getsource(decorator_reverser)
except:
    traceback.print_exc()
print
print inspect.getargspec(reverser)
print inspect.getsource(reverser)
print
print inspect.getargspec(adder)
print inspect.getsource(adder)
print
print inspect.getargspec(decorator_adder)
try:
    print inspect.getsource(decorator_adder)
except:
    traceback.print_exc()

print adder(1, 2)
