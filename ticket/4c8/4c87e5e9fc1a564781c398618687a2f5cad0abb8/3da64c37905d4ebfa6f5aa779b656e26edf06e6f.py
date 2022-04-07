from twisted.internet import defer
from twisted.cred import portal, checkers, credentials
from twisted.protocols import http
from twisted.web import resource, util, error

from twisted.web import server

class BasicAuthError(error.ErrorPage):
    def __init__(self, basicRealm="default"):
        error.ErrorPage.__init__(self,
                                 http.UNAUTHORIZED,
                                 "Unauthorized",
                                 "401 Authentication required")
        self.basicRealm = basicRealm

    def render(self, request):
        request.setHeader('WWW-authenticate',
                          'Basic realm="%s"' % self.basicRealm)
        return error.ErrorPage.render(self, request)

class BasicAuthWrapper:
    """Basic authentication wrapper.

    Proxies for the resource the portal returns from login. (the avatar)
    """

    __implements__ = resource.IResource

    isLeaf = 0    
    def __init__(self, portal, basicRealm="default"):
        self.portal = portal
        self.basicRealm = basicRealm

    def _login(self, request):
        def loginSuccess(result):
            interface, avatar, logout = result
            return avatar

        def loginFailure(error):
            return BasicAuthError(self.basicRealm)
            
        username = request.getUser()
        password = request.getPassword()

        d = self.portal.login(credentials.UsernamePassword(username, password),
                              None,
                              resource.IResource)
        d.addCallbacks(loginSuccess, loginFailure)

        return d
    
    def render(self, request):
        def renderPage(resc):
            result = resc.render(request)
            if result != server.NOT_DONE_YET:
                request.write(result)
                request.finish()

        d = self._login(request)
        d.addCallback(renderPage)
        
        return server.NOT_DONE_YET
    
    def getChildWithDefault(self, path, request):
        d = self._login(request)
        d.addCallback(lambda resc: resc.getChildWithDefault(path, request))

        return util.DeferredResource(d)

    def putChild(self, path, child):
        raise NotImplemented("putChild not implemented")

class SimpleBasicAuthWrapper(BasicAuthWrapper):
    """Simple basic authentication wrapper.

    Proxies for the resource we wrap, if we passed authentication.
    """
    def __init__(self, resc, checker, basicRealm="default"):
        self.checker = checker
        self.basicRealm = basicRealm
        self.resource = resc

    def _login(self, request):
        def loginSuccess(avatarId):
            return self.resource
        
        def loginFailure(error):
            return BasicAuthError(self.basicRealm)
        
        username = request.getUser()
        password = request.getPassword()

        d = defer.maybeDeferred(self.checker.requestAvatarId,
                                credentials.UsernamePassword(username, password))
        d.addCallbacks(loginSuccess, loginFailure)
        return d
