# Copyright (c) 2002 Neil Blakey-Milner
# Some minor modifications by Federico Di Gregorio.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS `AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
    
"""Simple CGI Protocol Implementation

This module provides an SCGIChannel class that can be used by twisted.web
to answer to SCGI requests from Apache mod_scgi. A classical pattern of
usage is to set a Site object protocol attribute to the SCGIChannel class.

This module only provides the server part of the protocol (the client
being Apache mod_scgi.)

Maintainer: U{Federico Di Gregorio<mailto:fog@initd.org>}
"""

from twisted.protocols import http
	
class SCGIChannel(http.HTTPChannel):
    """A receiver for HTTP requests over SCGI channel."""

    prefix = ''
    
    def __init__(self):
	http.HTTPChannel.__init__(self)
	self._buffer = ""
	self._maxbufferlength = None
					    
    def dataReceived(self, data):
	self._buffer = self._buffer + data
	if not self._maxbufferlength:
	    idx = self._buffer.index(":")
	    if not idx:
		return
	    self._maxbufferlength = long(self._buffer[:idx])
	    
	if len(self._buffer) - (idx + 2) == self._maxbufferlength:
	    scgistring = self._buffer[idx + 1:]
	    items = scgistring.split("\0")
	    items = items[:-1]
	    assert len(items) % 2 == 0, "malformed headers"
	    env = {}
	    for i in range(0, len(items), 2):
		env[items[i]] = items[i+1]
		
	    request = self.requestFactory(self, len(self.requests))
	    self.requests.append(request)
	    
	    if env.has_key("CONTENT_LENGTH"):
		request.received_headers["Content-Length"] = env["CONTENT_LENGTH"]
		
	    # translate aall HTTP_ heade namess into the official ones
	    for name, value in env.items():
		if name.startswith('HTTP_'):
		    name = name[5:].replace('_', ' ').title().replace(' ', '-')
		    if name == 'Host': name = 'host' # don't ask me why
		    request.received_headers[name] = value

	    self.transport.setPeer(("INET", env["REMOTE_ADDR"], int(env["REMOTE_PORT"])))
	    self.transport.setHost(("INET", env["SERVER_NAME"], int(env["SERVER_PORT"])))

	    self._command = env["REQUEST_METHOD"]
	    self._version = env["SERVER_PROTOCOL"]
	    
	    self._path = self.transformPath(env["REQUEST_URI"])
	    	    
	    self.allHeadersReceived()
	    self.allContentReceived()
																																																											                    
    def requestDone(self, request):
	self.transport.loseConnection()
	    
    def connectionMade(self):
	self.transport = SCGITransport(self.transport)
	
    def transformPath(self, path):
	"""Called to permorm arbitrary transformations on the path.
	
	The default transformation is to remove the 'prefix' class
	attribute from the path. The default value for 'prefix' is the
	empty string, meaning that the default transformation is identity
	(basiccaly you get the exact same path Apache was asked for.)
	
	Subclass SCGIChannel and redefine 'prefix' to remove an arbitrary 
	prefix (classical usage) or directly override this method for more
	complex transformations.
	"""
	# all the checks below are probably meaningless
	if self.prefix and path.startswith(self.prefix):
	    return path[len(self.prefix):]
	else:
	    return path

class SCGITransport:
    def __init__(self, real_transport):
	self._transport = real_transport
	self.firstline = 1
			    
    def write(self, data):
	if self.firstline:
	    data = data.replace("HTTP/1.1", "Status:")
	    self.firstline = 0
	self._transport.write(data)
	
    def writeSequence(self, data):
	for entry in data:
	    self.write(entry)
	    
    def setPeer(self, peer):
	self.peer = peer
		
    def setHost(self, host):
	self.host = host
				
    def getPeer(self):
	return self.peer
					    
    def getHost(self):
	return self.host
    
    def loseConnection(self):
	self._transport.loseConnection()
