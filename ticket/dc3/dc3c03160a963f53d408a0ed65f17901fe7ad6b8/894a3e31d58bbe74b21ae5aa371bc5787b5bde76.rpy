from twisted.web.resource import Resource
from twisted.web.static import Data

class Never(Resource):
	def render_GET(self, request):
		return 1

resource = Data('', 'text/plain')
resource.putChild('never', Never())
resource.putChild('', resource)
