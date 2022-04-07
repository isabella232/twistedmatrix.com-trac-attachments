# Copyright (c) 2001-2011 Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.trial import unittest

from twisted.words.protocols.jabber.jstrports import parse


class JabberStrPortsPlaceHolderTest(unittest.TestCase):
    """
    Tests for L{jstrports}
    """

    def test_parse(self):
        parse_params = ("tcp:DOMAIN:65535", "Factory")
        expected = ('TCP', ('DOMAIN', 65535, 'Factory'), {})
        self.assertEqual(parse(*parse_params), expected)

