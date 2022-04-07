    def cleanupDTP(self):
        """call when DTP connection exits
        """
        log.msg('cleanupDTP', debug=True)

        log.msg(self.dtpPort)
        dtpPort, self.dtpPort = self.dtpPort, None
        if interfaces.IListeningPort.providedBy(dtpPort):
            dtpPort.stopListening()
        elif interfaces.IConnector.providedBy(dtpPort):
            dtpPort.disconnect()
        else:
            assert False, "dtpPort should be an IListeningPort or IConnector, instead is %r" % (dtpPort,)

        self.dtpFactory.stopFactory()
        self.dtpFactory = None

        if self.dtpInstance is not None:
            self.dtpInstance.transport.abortConnection()
            self.dtpInstance = None

