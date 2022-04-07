#!/usr/bin/env python

from functools import partial

from twisted.internet import gtk3reactor
gtk3reactor.install()

from twisted.internet import reactor
from gi.repository import Gtk, Gio

def hello_cb(widget, data=None):
    print 'hello', widget

app = Gtk.Application(
            application_id='eu.elbl.ci.play',
            flags=Gio.ApplicationFlags.FLAGS_NONE)
app.connect('activate', hello_cb)

#app.run(None) # running without twisted works fine
reactor._run = partial(app.run, None) # without this, the process hangs forever
reactor.run()
