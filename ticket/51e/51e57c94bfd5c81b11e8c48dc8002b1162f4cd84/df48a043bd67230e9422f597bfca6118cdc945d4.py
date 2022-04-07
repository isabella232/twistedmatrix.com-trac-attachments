# -*- test-case-name: twisted.web.test -*-
# Copyright (c) 2008 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Interface definitions for L{twisted.web}.
"""

from zope.interface import Attribute

from twisted.internet.interfaces import IConsumer

class IRequest(IConsumer):
    """
    """
    method = Attribute("")
    uri = Attribute("")
    path = Attribute("")
    args = Attribute("")

    received_headers = Attribute("")
    requestHeaders = Attribute("")

    headers = Attribute("")
    responseHeaders = Attribute("")

    def getHeader(name):
        pass


    def getCookie(key):
        pass


    def finish():
        pass


    def addCookie(k, v, expires=None, domain=None, path=None, max_age=None, comment=None, secure=None):
        pass


    def setResponseCode(code, message=None):
        pass


    def setHeader(k, v):
        pass


    def redirect(url):
        pass


    def setLastModified(when):
        pass


    def setETag(etag):
        pass



    def getAllHeaders():
        pass


    def getRequestHostname():
        pass


    def getHost():
        pass


    def setHost(host):
        pass


    def getClientIP():
        pass


    def isSecure():
        pass


    def getUser():
        pass


    def getPassword():
        pass


    def getClient():
        pass


    def notifyFinish():
        pass


    def getSession():
        pass


    def prePathURL():
        pass


    def URLPath():
        pass


    def rememberRootURL():
        pass


    def getRootURL():
        pass
