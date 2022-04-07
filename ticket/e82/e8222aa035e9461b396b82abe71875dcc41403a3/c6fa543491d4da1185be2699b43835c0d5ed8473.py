from twisted.internet.glib2reactor import install
install()
from twisted.internet.utils import getProcessOutput
from twisted.internet import reactor


def main():
    def print_output(output):
        print output
    result = getProcessOutput("/bin/ls", args=["/"])
    result.addCallback(print_output)
    reactor.run()


if __name__ == "__main__":
    main()


