#!/usr/bin/python

from zope.interface import implements
from twisted.web2.iweb import IRequest
from twisted.web2.stream import SimpleStream
from twisted.web2.http_headers import Headers

#################################################################
##  Define a very simplistic Request class that can be fed to  ##
##  other routines below.                                      ##
#################################################################

class MyRequest(object):
	implements(IRequest)
	def __init__(self, method):
		self.method = method
		self.uri = "http://localhost"
		self.clientproto = "HTTP/1.1"
		self.headers = Headers()
		self.stream = SimpleStream()
		self.stream.length = 0
		self.chanRequest = None
		self.remoteAddr = "127.0.0.1"
	def writeResponse(self, response):
		print "Writing response..."

# We want to simulate the GET and PROPFIND methods in these tests.
get_request = MyRequest("GET")
propfind_request = MyRequest("PROPFIND")


#####################################################################
##  Define a simple resource that can also handle PROPFIND method  ##
##  requests. This is used to simulate a DAV resource.             ##
#####################################################################

from twisted.web2.resource import LeafResource
class MyResource(LeafResource):
	def checkPreconditions(self, request):
		pass
	def render(self, request):
		print "Rendering MyResource..."
	def http_PROPFIND(self, request):
		print "Handling PROPFIND method..."

###################
##  BEGIN TESTS  ##
###################

##
## TEST #1: Create a resource and call renderHTTP() method for a
## GET request and a PROPFIND request.  Also check that the list of
## allowed methods is correct.
##
print "\n\n*** Test #1 ***"

resource = MyResource()

# Should print "Rendering MyResource..."
resource.renderHTTP(get_request)

# Should print "Handling PROPFIND method..."
resource.renderHTTP(propfind_request)

# The allowed methods should be "GET HEAD OPTIONS PROPFIND TRACE"
print "MyResource allowed methods = ", 
for m in resource.allowedMethods():
	print m,
print


##
## TEST #2: Create a HTTPAuthResource to wrap our original resource,
## and call renderHTTP() with a GET request. This should return a 
## UnauthorizedResource object.  Call renderHTTP() with same GET request
## on this new object.  We should get back a "UnauthorizedResponse 401"
## response.
##
print "\n\n*** Test #2 ***"

from twisted.web2.auth.wrapper import HTTPAuthResource
wrapper = HTTPAuthResource(resource, [], None, (None,) )
print wrapper.renderHTTP(get_request).renderHTTP(get_request)


##
## TEST #3: Use our previous wrapped resource and call renderHTTP() with 
## PROPFIND request. This should return a UnauthorizedResource object.  Call 
## renderHTTP() with same PROPFIND request on this new object.  We SHOULD get 
## back a "UnauthorizedResponse 401" response, but instead it will be "Not 
## Allowed 405".  In addition, the allowed methods will be incorrectly set to
## "GET HEAD OPTIONS TRACE".
##
print "\n\n*** Test #3 ***"

response = wrapper.renderHTTP(propfind_request).renderHTTP(propfind_request)
print response
print response.headers
