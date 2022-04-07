# Copyright (c) 2007 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Tests for the twisted.python.properties module
"""

from twisted.trial import unittest, util
from twisted.python.properties import deprecated_property

deprecation_message = "Deprecation Message"

def _getter(self):
    """A simple getter used as an argument to deprecated_property"""
    return None

def _setter(self, value):
    """A simple setter that ignores its value used as an argument
    to deprecated_property"""
    pass

def _deller(self):
    """A simple deller that ignores used as an argument to
    deprecated_property"""
    pass

def _getattr(c):
    """A getattr is implemented here, allowing the deprecation
    warnings to be issued for this __file__"""
    return c.x

def _setattr(c):
    """A setattr wrapper is implemented here, allowing the deprecation
    warnings to be issued for this __file__"""
    c.x = 1

def _delattr(c):
    """A delattr is implemented here, allowing the deprecation
    warnings to be issued for this __file__"""
    del c.x

class DeprecatedPropertyTests(unittest.TestCase):
    """
    Tests for deprecated properties.
    """

    def _verify(self, allowed, method, c):
        if allowed:
            self.assertWarns(DeprecationWarning, deprecation_message, __file__,
                             method, c)
        else:
            self.assertRaises(AttributeError, method, c)

    def test_access_limit(self):
        """
        Test that specifying no getter, setter or deller indeed
        prevents their access.
        """

        for getter in [None, _getter]:
            for setter in [None, _setter]:
                for deller in [None, _deller]:
                    class Container(object):
                        x = deprecated_property(deprecation_message, getter, setter, deller)
                    c = Container()
                    self._verify(bool(getter), _getattr, c)
                    self._verify(bool(setter), _setattr, c)
                    self._verify(bool(deller), _delattr, c)
