#!/usr/bin/python

from twisted.trial import unittest
from twisted.words.xish import xpath, domish

class XPathUnicodeTest(unittest.TestCase):

    def testMatchesUnicodePath(self):
        test_tag = u'\u043d\u0435\u043a\u0438\u0439_\u0442\u0435\u0433'
        el = domish.Element((None, test_tag))
        self.assertEquals(1, xpath.XPathQuery(u'/%s' % test_tag).matches(el))

    def testUnicodeContent(self):
        test_content = u'\u0442\u0435\u0441\u0442'
        el = domish.Element((None, 'iq'))
        el.addElement('query', content=test_content)
        self.assertEquals(test_content, xpath.XPathQuery('/iq/query').queryForString(el))
