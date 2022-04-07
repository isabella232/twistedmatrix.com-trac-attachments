# Copyright (c) 2001-2007 Twisted Matrix Laboratories.
# See LICENSE for details.


"""
Test web.tap support.
"""


from twisted.trial import unittest
from twisted.web import tap

class webTapTestCase(unittest.TestCase):
    def testMakeService(self):
        tap.makeService({'root' : False, 'logfile' : False, 'personal' : True, 'notracebacks' : True}) 
