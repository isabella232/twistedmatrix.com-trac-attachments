
from distutils.core import Extension

try:
    from twisted.python import dist
except ImportError:
    raise SystemExit("twisted.python.dist module not found.  Make sure you "
                     "have installed the Twisted core package before "
                     "attempting to install any other Twisted projects.")

def detectExtensions(builder):
    ## XXX-JE-CYGWIN-PATCH
    import sys
    extra_libraries = []
    if sys.platform == "cygwin":
        extra_libraries = [ "rpc" ]
    ## XXX-JE-CYGWIN-PATCH-END
    if builder._check_header("rpc/rpc.h"):
        return [Extension("twisted.runner.portmap",
                               ["twisted/runner/portmap.c"],
                               define_macros=builder.define_macros
                               ## XXX-JE-CYGWIN-PATCH
                               , libraries=extra_libraries)
                               ## XXX-JE-CYGWIN-PATCH-END
                               ]
    else:
        builder.announce("Sun-RPC portmap support is unavailable on this "
                      "system (but that's OK, you probably don't need it "
                      "anyway).")

if __name__ == '__main__':
    dist.setup(
        twisted_subproject="runner",
        # metadata
        name="Twisted Runner",
        description="Twisted Runner is a process management library and inetd replacement.",
        author="Twisted Matrix Laboratories",
        author_email="twisted-python@twistedmatrix.com",
        maintainer="Andrew Bennetts",
        maintainer_email="spiv@twistedmatrix.com",
        url="http://twistedmatrix.com/trac/wiki/TwistedRunner",
        license="MIT",
        long_description="""\
Twisted Runner contains code useful for persistent process management
with Python and Twisted, and has an almost full replacement for inetd.
""",
        # build stuff
        detectExtensions=detectExtensions,
    )
