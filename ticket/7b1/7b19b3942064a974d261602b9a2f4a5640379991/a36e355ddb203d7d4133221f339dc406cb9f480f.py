from twisted.application import service
from twisted.words.protocols.jabber import component, xmlstream
from twisted.words.xish import utility

from wokkel import disco
from wokkel.component import Component

class InternalComponent(xmlstream.XMPPHandlerCollection, service.Service):

    logTraffic = False

    def __init__(self, router, domain):
        xmlstream.XMPPHandlerCollection.__init__(self)
        self.router = router
        self.domain = domain

        self.xmlstream = None

    def startService(self):
        service.Service.startService(self)

        self.pipe = utility.XmlPipe()
        self.xmlstream = self.pipe.source
        self.router.addRoute(self.domain, self.pipe.sink)

        for e in self:
            e.makeConnection(self.xmlstream)
            e.connectionInitialized()


    def stopService(self):
        service.Service.stopService(self)

        self.router.removeRoute(self.domain, self.pipe.sink)
        self.pipe = None
        self.xmlstream = None

        for e in self:
            e.connectionLost(None)


    def addHandler(self, handler):
        xmlstream.XMPPHandlerCollection.addHandler(self, handler)

        if self.xmlstream:
            handler.makeConnection(self.xmlstream)
            handler.connectionInitialized()


    def send(self, obj):
        self.xmlstream.send(obj)



class DiscoClientSender(xmlstream.XMPPHandler):
    def connectionInitialized(self):

        def cb(result):
            print "Joepie"

        iq = xmlstream.IQ(self.xmlstream, 'get')
        iq['from'] = 'cmp2'
        iq['to'] = 'cmp1'
        iq.addElement((disco.NS_INFO, 'query'))
        d = iq.send()
        d.addCallback(cb)



application = service.Application("Jabber Router")

router = component.RouterService()
router.setServiceParent(application)

componentService = component.ComponentServer(router, port=5347)
componentService.logTraffic = True
componentService.setServiceParent(application)

#cmp1 = Component('localhost', 5347, 'cmp1', 'secret')
cmp1 = InternalComponent(router, 'cmp1')
cmp1.logTraffic = True
cmp1.setServiceParent(application)
disco.DiscoHandler().setHandlerParent(cmp1)

cmp2 = Component('localhost', 5347, 'cmp2', 'secret')
#cmp2 = InternalComponent(router, 'cmp2')
cmp2.logTraffic = True
cmp2.setServiceParent(application)
DiscoClientSender().setHandlerParent(cmp2)
