if __name__ == "__main__":
    from twisted.internet import glib2reactor
    glib2reactor.install()
    reactor.run()
