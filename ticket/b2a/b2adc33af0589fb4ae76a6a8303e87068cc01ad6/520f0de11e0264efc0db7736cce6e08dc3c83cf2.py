import sys

from twisted.conch.ssh.keys import Key


if __name__ == "__main__":
    phrase = None
    fn = sys.argv[1]

    if len(sys.argv) == 3:
        phrase = sys.argv[2]

    key = Key.fromFile(fn, passphrase=phrase)

    print "File: %s" % fn
    print "Type: %s" % key.type()
    print "Fingerprint: %s" % key.fingerprint()
