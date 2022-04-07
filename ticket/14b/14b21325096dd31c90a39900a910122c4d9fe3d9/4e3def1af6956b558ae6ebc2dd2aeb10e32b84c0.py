import sys
import twisted.scripts._twistw as twistw
from twisted.application import app

class ExeArcServerOptions(twistw.ServerOptions):
    synopsis = "Usage: twistd.exe [options]"

    for path in sys.path:
        if '.zip' in path:
            optParameters = [['zipfile','z', path,
                              "Read python byte code from a zipfile"]]
            break

    
    def opt_version(self):
        """Print version information and exit.
        """
        print 'twistd.exe (the Twisted Windows runner) %s' % copyright.version
        print copyright.copyright
        sys.exit()


def run():
    app.run(twistw.runApp, ExeArcServerOptions)
    
if __name__ == "__main__":
    run()