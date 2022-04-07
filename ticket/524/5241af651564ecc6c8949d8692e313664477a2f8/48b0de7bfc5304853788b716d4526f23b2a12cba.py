# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.trial import unittest

from twisted.mail.pb import MaildirClient

"""Test failure of method calls on MaildirBroker object."""

from twisted.mail.pb import MaildirBroker

class ProtoGetCollectionTestCase(unittest.TestCase):
    """
    verifies that proto_getCollection throws an attribute error
    """

    def testAttributeError(self):
        mb = MaildirBroker()
        self.assertRaises(AttributeError,
                          MaildirBroker.proto_getCollection,
                          mb,
                          None,
                          None,
                          None,
                          None)


class GetCollectionTestCase(unittest.TestCase):

    """
    verifies that getCollection throws an attribute error
    """

    def testAttributeError(self):
        mb = MaildirBroker()
        self.assertRaises(AttributeError,
                          MaildirBroker.getCollection,
                          mb,
                          None,
                          None,
                          None)
