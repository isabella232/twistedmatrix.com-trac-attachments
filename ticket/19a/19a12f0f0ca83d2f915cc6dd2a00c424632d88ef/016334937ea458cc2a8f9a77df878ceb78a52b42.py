# encoding: utf-8
import os

ROOT_PATH = os.path.abspath(os.path.join(os.path.split(__file__)[0],'..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'web.settings'

from twisted.internet import iocpreactor
iocpreactor.install()

from twisted.application import internet, service, app
from twisted.web import server, wsgi, resource, static
from twisted.python import threadpool, log
from django.core.handlers.wsgi import WSGIHandler
from django.conf import settings

from twisted.internet import reactor
    
class DjangoRootResource(resource.Resource):
    isLeaf = True

    def __init__(self, wsgi_resource, staticDict={}):
        # I don't understand why super() doesn't work here.  old-style classes in twisted?!
        resource.Resource.__init__(self)
        self.staticDict = staticDict
        self.wsgi_resource = wsgi_resource

    def render(self, request):
        for overlay in self.staticDict:
            overlayList = overlay.split("/")
            if overlayList[0] == "":
                _ = overlayList.pop(0)
            for a, b in zip(overlayList, request.postpath):
                if a != b:
                    break
            else:
                # http://www.mail-archive.com/twisted-web@twistedmatrix.com/msg02063.html
                return resource.getChildForRequest(self.staticDict[overlay], request).render(request)
        else:
            return resource.getChildForRequest(self.wsgi_resource, request).render(request)


def wsgi_resource():
    pool = threadpool.ThreadPool(minthreads=8, maxthreads=40, name="WSGI")
    pool.start()
    # Allow Ctrl-C to get you out cleanly:
    reactor.addSystemEventTrigger('after', 'shutdown', pool.stop)
    wsgi_resource = wsgi.WSGIResource(reactor, pool, WSGIHandler())
    return wsgi_resource

        
def main():    
    # Twisted Application Framework setup:
    application = service.Application('webservice')
    
    root = DjangoRootResource(wsgi_resource(), {
        "/favicon.ico": static.File(os.path.join(ROOT_PATH,'components','web','media','img')),
        "/media": static.File(os.path.join(ROOT_PATH,'components','web')),
        "/admin-media": static.File(os.path.join(ROOT_PATH,'3rdparty','django','contrib')),
    })
            
    # Serve it up:
    main_site = server.Site(root)
    wsgi_service = internet.TCPServer(settings.SERVER_PORT, main_site)
    wsgi_service.setServiceParent(application)
    
    app.startApplication(application, False)
    
    reactor.run()
    
if __name__ == '__main__':
    main()
