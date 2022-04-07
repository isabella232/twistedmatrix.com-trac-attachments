#!/usr/bin/env python
# same as -test, but use twisted's glib reactor

import sys

from twisted.internet import glib2reactor # for non-GUI apps
glib2reactor.install()

from twisted.internet import reactor
from twisted.python import log

import dbus, gobject
# see pydoc dbus.mainloop.glib
# have to setup an event loop for dbus or else..
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

def my_chat_func(account, sender, message, conversation, flags):
    print sender, 'said:', message

def my_priv_func(account, sender, message, conversation, flags):
    print sender, 'said in private:', message

def main():
    try:
        bus = dbus.SessionBus()
        bus.add_signal_receiver(my_chat_func,
            dbus_interface='im.pidgin.purple.PurpleInterface',
            signal_name='ReceivingChatMsg')
        bus.add_signal_receiver(my_priv_func,
            dbus_interface='im.pidgin.purple.PurpleInterface',
            signal_name='ReceivingImMsg')
        reactor.callLater( 30, reactor.stop )
    except:
        reactor.stop()
        raise

if ( __name__ == '__main__' ):
    log.startLogging( sys.stdout )
    reactor.callWhenRunning( main )
    reactor.run()
