
class NonStreamingRequest(object):
      def __init__(self, streamingRequest, bytes):
      	  # set up all old request attributes
	  self.content = StringIO(bytes)


class OldToNew:
      def __init__(self, wrapped, segments=None):
      	  self.wrapped = wrapped
	  self.segments = segments or []

      def getChild(self, name, request):
      	  return OldToNew(self.wrapped, self.segments + [name])


      def render(self, request):
      	  d = self.request.body.startProducing(self)
	  def cbProduced(ignored):
	      oldRequest = NonStreamingRequest(request, self.bytes)
	      resource = self.wrapped
	      for path in self.segments:
	      	  resource = resource.getChild(path, oldRequest)
	      result = resource.render(NonStreamingRequest(request, self.bytes))
	      # process result
	  d.addCallback(cbProduced)
	  return NOT_DONE_YET
      	  

      def write(self, bytes):
            self.bytes += bytes
      


class Request:
      def allHeadersReceived(self):
      	  # parse url
	  resource = IStreamingResource(self.site.resource)
	  while urlSegments:
	  	resource = resource.getChild(urlSegments.pop(0), self)
	  if urlSegments:
	     resource = NonStreamingWrapper(resource)
	  resource.render(self)



      def allHeadersReceived(self):
      	  # parse url
	  resource = self.site.resource
	  while urlSegments and IStreamingResource.providedBy(resource):
	  	resource = resource.getChild(urlSegments.pop(0))
	  if urlSegments:
	     resource = NonStreamingWrapper(resource)
	  resource.render(self)



