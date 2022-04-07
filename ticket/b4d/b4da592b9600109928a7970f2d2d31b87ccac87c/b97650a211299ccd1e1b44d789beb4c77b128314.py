#!/usr/bin/python

from twisted.spread import jelly
import types
from new import instance

_NO_STATE = jelly._NO_STATE

def monkeyPatchedNewInstance(cls, state=_NO_STATE):
    """
    Make a new instance of a class without calling its __init__ method.
    Supports both new- and old-style classes.

    @param state: A C{dict} used to update C{inst.__dict__} or C{_NO_STATE}
        to skip this part of initialization.

    @return: A new instance of C{cls}.
    """
    if not isinstance(cls, types.ClassType):
        # new-style
        inst = cls.__new__(cls)

        if state is not _NO_STATE:
            for k,v in inst.__dict__.iteritems():
                if k not in state:
                    state[k] = v
            inst.__dict__ = state

    else:
        if state is not _NO_STATE:
            inst = instance(cls, state)
        else:
            inst = instance(cls)
    return inst

## Uncomment the following line to demonstrate the patch
#jelly._newInstance = monkeyPatchedNewInstance

class Foo(object): pass
class Bar(object): pass
class Baz: pass
class Qux: pass

def test0():
    # dict / dict
    x = {}
    x['bar'] = {}
    x['bar']['foo'] = x

    J = jelly.jelly(x)
    y = jelly.unjelly(J)

    return y['bar']['foo'] == y

def test1():
    # Object / Object
    x = Foo()
    x.bar = Bar()
    x.bar.foo = x

    J = jelly.jelly(x)
    y = jelly.unjelly(J)
    return y.bar.foo == y

def test2():
    # Object / dict
    x = Foo()
    x.dict = {}
    x.dict['foo'] = x

    J = jelly.jelly(x)
    y = jelly.unjelly(J)
    return y.dict['foo'] == y

def test3():
    # dict / object
    x = {}
    x['foo'] = Foo()
    x['foo'].dict = x

    J = jelly.jelly(x)
    y = jelly.unjelly(J)
    return y['foo'].dict == y

def test4():
    # old-style class / old-style class

    x = Baz()
    x.qux = Qux()
    x.qux.baz = x

    J = jelly.jelly(x)
    y = jelly.unjelly(J)

    return y.qux.baz == y

if __name__ == '__main__':
    # All of these tests should return True
    print test0()
    print test1() # Fails
    print test2()
    print test3() # Fails
    print test4()
