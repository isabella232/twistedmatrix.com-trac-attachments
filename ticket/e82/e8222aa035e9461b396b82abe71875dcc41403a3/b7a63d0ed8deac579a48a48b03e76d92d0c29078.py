import signal
import os

from twisted.internet.glib2reactor import install
install()
from twisted.internet import reactor


def main():
    reactor.callLater(1, lambda: os.kill(os.getpid(), signal.SIGCHLD))
    reactor.run()


if __name__ == "__main__":
    main()

