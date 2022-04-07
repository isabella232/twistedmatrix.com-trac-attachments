import random
from twisted.web import resource, server

DOC = '/tmp/tmpZuSk7B'
CRLF = '\r\n'

class InProgressIdx(resource.Resource):
        def render_GET(self, request):
                self.ChunkedDeliverIndex(request)
                return server.NOT_DONE_YET

        def ChunkedDeliverIndex(self, request):
                f = open(DOC)
                while 1:
                        chunk_size = random.randint(100, 1000)
                        chunk_data = f.read(chunk_size)
                        if len(chunk_data) != chunk_size:
                                chunk_size = len(chunk_data)
                        if chunk_size == 0:
                                request.write('0' + CRLF)
                                break
                        request.write(chunk_data)
                request.finish()
                f.close()

resource = InProgressIdx()
