class MyIMAPCommand(twisted.mail.imap4.Command):
    def finish(self, lastLine, unusedCallback):
        send = []
        unuse = []
        for L in self.lines:
            names = twisted.mail.imap4.parseNestedParens(L)
            N = len(names)
            # could be suboptimal to use wantResponse for OK appendices as well...
            if (N >= 1 and names[0] in self.wantResponse or
                N >= 2 and 'OK' and isinstance(names[1], types.ListType) and names[1][0] in self.wantResponse):
                send.append(L)
            else:
                unuse.append(L)
        d, self.defer = self.defer, None
        d.callback((send, lastLine))
        if unuse:
            unusedCallback(unuse)
