from twisted.application.service import IServiceMaker, Service
from twisted.plugin import IPlugin
from twisted.python.usage import Options
from zope.interface import implements


class Gtk2HelloWorld:
    implements(IServiceMaker, IPlugin)

    tapname = 'gtk2hello'
    description = 'gtk2 hello world example'
    options = Options

    def makeService(self, options):
        import gtk
        w = gtk.Window()
        lbl = gtk.Label('hello world')
        w.add(lbl)
        w.show_all()
        return Service()


hw = Gtk2HelloWorld()
