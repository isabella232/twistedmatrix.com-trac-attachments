import sys
import shutil
import hotshot
import profile
import marshal
import tempfile

from twisted.python import components

class IProfiler(components.Interface):
    def start(self):
        """Begin recording profiling information.
        """

    def stop(self):
        """Stop recording profiling information.
        """

    def save(self, fileObj):
        """Save recorded profiling information to the given file.
        """

from twisted.application import service

class OldProfilerService(service.Service):
    __implements__ = service.Service.__implements__, IProfiler

    def __init__(self):
        self.setName("atop.tpython.ProfilerService")
        self.profile = profile.Profile()

    def start(self):
        sys.setprofile(self.profile.dispatch)

    def stop(self):
        sys.setprofile(None)

    def save(self, fileObj):
        marshal.dump(self.profile.stats, fileObj)

class HotshotProfilerService(service.Service):
    __implements__ = service.Service.__implements__, IProfiler

    running = False

    def __init__(self, filename=None):
        self.setName("atop.tpython.HotshotProfilerService")
        if filename is None:
            foo, self.fn = tempfile.mkstemp('hotshot')

    def start(self):
        self.profile = hotshot.Profile(self.fn)
        self.profile.start()
        self.running = True 

    def stop(self):
        self.profile.stop()
        self.running = False

    def save(self, fileObj):
        # XXX - Could this end up copying partial records?
        shutil.copyfileobj(file(self.fn, 'rb'), fileObj)
