#!/usr/bin/env python
# from twisted.internet import default
# default.install()

import dbus
import dbus.service
import dbus.glib
import gobject

# Installs the event loop that can be used both by dbus and twisted
from twisted.internet import glib2reactor
# For some reason this isn't done automatically
reactor = glib2reactor.install()

from twisted.internet import protocol
from twisted.web import server, resource

# We use these to report back to the caller
webrequest = None
dbusrequest = None

# This is EchoClient from Twisted docs
class EchoClient(protocol.Protocol):
    def connectionMade(self):
        self.transport.write("hello, world!")
    
    def dataReceived(self, data):
        print "Server said:", data
        if webrequest != None:
            webrequest.write(data)
        if dbusrequest != None:
            dbusrequest(data)
        self.transport.loseConnection()
    
    def connectionLost(self, reason):
        global webrequest, dbusrequest
        print "connection lost"
        if webrequest != None:
            webrequest.finish()
            webrequest = None
        dbusrequest = None

class EchoFactory(protocol.ClientFactory):
    protocol = EchoClient

#  This is example-service.py from DBus Python bindings
class SomeObject(dbus.service.Object):
    def __init__(self, bus_name, object_path="/SomeObject"):
        dbus.service.Object.__init__(self, bus_name, object_path)

    @dbus.service.method("org.designfu.TwSampleInterface", async_callbacks=('dbus_async_cb', 'dbus_async_err_cb'))
    def HelloWorld(self, hello_message, dbus_async_cb, dbus_async_err_cb):
        print "dbus request"
        global webrequest, dbusrequest
        webrequest = None
        dbusrequest = dbus_async_cb
        f = EchoFactory()
        print (str(hello_message))
        reactor.connectTCP("127.0.0.1", 9090, f)
        return None

    @dbus.service.method("org.designfu.TwSampleInterface")
    def GetTuple(self):
        return ("Hello Tuple", " from example-service.py")

    @dbus.service.method("org.designfu.TwSampleInterface")
    def GetDict(self):
        return {"first": "Hello Dict", "second": " from example-service.py"}

class Login(resource.Resource):

    def render_GET(self, request):
        global webrequest
        webrequest = request
        dbusrequest = None
        print "web request"
        f = EchoFactory()
        reactor.connectTCP("127.0.0.1", 9090, f)
        return server.NOT_DONE_YET

class DBusClient(resource.Resource):

    def render_GET(self, request):
        print "web dbus client"
        #  This is example-client.py from DBus Python bindings
        bus = dbus.SessionBus()
        remote_object = bus.get_object("org.designfu.SampleService", "/SomeObject")
        iface = dbus.Interface(remote_object, "org.designfu.SampleInterface")
        hello_reply_list = remote_object.HelloWorld("Hello from example-client.py!", dbus_interface = "org.designfu.SampleInterface")
        hello_reply_tuple = iface.GetTuple()
        hello_reply_dict = iface.GetDict()
        request.write(str(hello_reply_list))
        request.write(str(hello_reply_tuple))
        request.write(str(hello_reply_dict))
        request.finish()
        return server.NOT_DONE_YET

session_bus = dbus.SessionBus()
name = dbus.service.BusName("org.designfu.TwSampleService", bus=session_bus)
object = SomeObject(name)

root = resource.Resource()
root.putChild('login', Login())
root.putChild('dbus', DBusClient())

site = server.Site(root)

reactor.listenTCP(8080, site)
reactor.run()

