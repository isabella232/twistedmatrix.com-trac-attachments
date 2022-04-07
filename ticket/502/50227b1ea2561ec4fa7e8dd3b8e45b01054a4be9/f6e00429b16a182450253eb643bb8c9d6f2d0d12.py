#!/usr/bin/env python3

from twisted.spread.jelly import jelly

import inspect

class A:
    """
    Dummy class.
    """

    def amethod(self):
        pass

am = A.amethod

print(am)
print('type:', type(am))
print('repr:', repr(am))
print('__name__:', am.__name__)
print('inspect.ismethod(am):', inspect.ismethod(am))
print('inspect.isfunction(am):', inspect.isfunction(am))
print()
print('jelly:', jelly(am))

