#!/usr/bin/env python

import gobject
import pygtk
import gtk

# twisted imports
from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

# system imports
import time, sys


class GUI(object):
	def __init__(self):
		self.mw = gtk.Window()
		self.mw.connect('destroy', self.quit)
		bt = gtk.Button('Run ls')
		bt.connect('clicked', self.on_click)
		frame = gtk.Frame()
		frame.add(bt)
		self.mw.add(frame)
		self.mw.show_all()
		reactor.run()

	def on_click(self, b):
		def processEnded(*args):
			print "processEnded"
		proto = protocol.ProcessProtocol()
		proto.processEnded = processEnded
		reactor.spawnProcess(proto, 'ls', ['/bin/ls'], None)	
		print 'clicked'

	def quit(self, w):
		print 'closeapp'
		try:
			reactor.stop()
		except:
			pass
		gtk.main_quit()


if __name__ == '__main__':
	GUI()
	gtk.main()
