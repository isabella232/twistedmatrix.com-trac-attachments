from twisted.web.woven.controller import Controller
from twisted.web.woven.model import MethodModel
from twisted.web.static import FileTransfer
from twisted.web.server import NOT_DONE_YET
from twisted.web.resource import Resource
import cStringIO, math

class VirtualFile(Resource):
    def __init__(self):
        self.data = cStringIO.StringIO("testcrud\x93\x8c"*50000)
        self.datalength = len(self.data.getvalue())

    def render(self, request):
        request.setHeader('content-type', 'application/octet-stream')
	print "----File size should be about %d bytes" % self.datalength
        FileTransfer(self.data, self.datalength, request)

    def getChild(self, name, request):
        return None
    

class MyController(Controller):
    def __init__(self):
        Controller.__init__(self, MethodModel())

    def getChild(self, name, request):
        return VirtualFile()

resource = MyController()
