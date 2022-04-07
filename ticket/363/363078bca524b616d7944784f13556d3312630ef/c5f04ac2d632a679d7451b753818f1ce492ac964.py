#!/usr/bin/python

import os
from twisted.internet import reactor
from twisted.web2 import server, http, resource, channel
from twisted.web2 import http_headers, responsecode
from twisted.web2 import iweb, stream

SAVEDIR = "/tmp" 
READSIZE=8192

class UploadFile(resource.PostableResource):
	def render(self, ctx):
		request = iweb.IRequest(ctx)
		filename = request.files['filename'][0][0]
		file = request.files['filename'][0][2]

		filestream = stream.FileStream(file)
		dest = os.path.join(SAVEDIR,filename)
		destfile = os.fdopen(os.open(dest,
				os.O_WRONLY | os.O_CREAT | os.O_EXCL,
				0644), 'w', 0)
		stream.readIntoFile(filestream, destfile)

		msg = "saved %s to %s" % (filename, dest)
		print msg
		return http.Response(stream="%s" % msg)

class Toplevel(resource.Resource):
	addSlash = True
	def render(self, ctx):
		return http.Response(responsecode.OK,
				{'content-type': http_headers.MimeType('text', 'html')},
				"Hello")
	
	child_uploadfile = UploadFile()

if __name__ == "__main__":
	site = server.Site(Toplevel())
	reactor.listenTCP(1080, channel.HTTPFactory(site))
	reactor.run()
