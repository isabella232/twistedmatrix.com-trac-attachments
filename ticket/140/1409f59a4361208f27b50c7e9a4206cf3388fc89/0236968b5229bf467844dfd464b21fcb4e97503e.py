#!/usr/bin/env python

from functools import partial

from twisted.internet import gtk3reactor
gtk3reactor.install()

from twisted.internet import reactor
from gi.repository import Gtk, Gio

def hello_cb(widget, data=None):
    print 'hello', widget

def hello():
    print 'hello reactor'

app = Gtk.Application(
            application_id='eu.elbl.ci.play',
            flags=Gio.ApplicationFlags.FLAGS_NONE)
app.connect('activate', hello_cb)

window = Gtk.Window(title='Hello')
window.show_all()
app.add_window(window)

reactor.callLater(1, hello)

#app.run(None) # running without twisted works fine
#reactor._run = partial(app.run, None) # without this, the app's activate event never fires
reactor.run()
