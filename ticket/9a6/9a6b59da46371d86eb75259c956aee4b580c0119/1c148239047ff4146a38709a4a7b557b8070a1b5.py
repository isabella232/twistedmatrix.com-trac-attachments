__all__ = ['install']

# System Imports
import sys
try:
    if not hasattr(sys, 'frozen'):
        # Don't want to check this for py2exe
        import pygtk
        pygtk.require('2.0')
except (ImportError, AttributeError):
    pass # maybe we're using pygtk before this hack existed.
import gobject
if hasattr(gobject, "threads_init"):
    # recent versions of python-gtk expose this. python-gtk=2.4.1
    # (wrapping glib-2.4.7) does. python-gtk=2.0.0 (wrapping
    # glib-2.2.3) does not.
    gobject.threads_init()

from twisted.internet import win32eventreactor
# the next callback
_simtag = None

class Win32Gtk2Reactor(win32eventreactor.Win32Reactor):
    """Reactor that works on Windows.

    input_add is not supported on GTK+ for Win32, apparently.
    """

    def crash(self):
        import gtk
        # mainquit is deprecated in newer versions
        if hasattr(gtk, 'main_quit'):
            gtk.main_quit()
        else:
            gtk.mainquit()

    def run(self, installSignalHandlers=1):
        import gtk
        self.startRunning(installSignalHandlers=installSignalHandlers)
        self.simulate()
        # mainloop is deprecated in newer versions
        if hasattr(gtk, 'main'):
            gtk.main()
        else:
            gtk.mainloop()

    def simulate(self):
        """Run simulation loops and reschedule callbacks.
        """
        global _simtag
        if _simtag is not None:
            gobject.source_remove(_simtag)
        self.iterate()
        timeout = min(self.timeout(), 0.1)
        if timeout is None:
            timeout = 0.1
        # grumble
        _simtag = gobject.timeout_add(int(timeout * 1010), self.simulate)


def install(useGtk=True):
    """Configure the twisted mainloop to be run inside the gtk mainloop.
    """
    reactor = Win32Gtk2Reactor()
    from twisted.internet.main import installReactor
    installReactor(reactor)
    return reactor

