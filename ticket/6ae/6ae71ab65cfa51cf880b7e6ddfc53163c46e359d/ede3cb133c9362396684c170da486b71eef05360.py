'''
ReadlineIO: a complement to twisted.internet.stdio.StandardIO that
polls/selects for events and uses the callback interface of readline
for actually reading/getting events.

Currently, it accesses the callback interface using ctypes on unix,
while on Windows a patched emacs.py is needed
(Posted by Jorgen on the IPython-devel list).

This is only possible with monkey patching, and for Windows it also relies
on the patches from ticket #2157.

Some sensible future steps:

1) expose the callback interface in the readline module in the Python
   standard library (see sf.net feature request 1713877),
2) use exactly the same interface in the windows version pyreadline
   (posted to the IPython-devel list),
3) inclusion of windows pyreadline in the standard library (todo).

:author: strank
'''

__docformat__ = "restructuredtext en"

from readlinecallbackapi import do_the_monkeypatch_dance
do_the_monkeypatch_dance()

import os
import readline

from twisted.internet import reactor, stdio
from twisted.protocols import basic

if sys.platform == 'win32':
    import msvcrt
    import win32console
    from twisted.internet import _pollingfile, _win32stdio


def main():
    '''For interactive testing only.'''
    sp = ShellProtocol()
    #sp.setRawMode()
    ReadlineIO(sp)
    reactor.run()


class ReadlineReader(_pollingfile._PollableReader):
    def __init__(self, channel, receivedCallback, lostCallback, prompt=''):
        _pollingfile._PollableReader.__init__(self, channel.handle,
                                              receivedCallback, lostCallback)
        self.channel = channel
        self.prompt = prompt
        self.lastdatalen = 0
        self.do_prompt() # also installs the callback

    def do_prompt(self, prompt=None):
        if prompt is None:
            prompt = self.prompt
        readline.callback_handler_install(prompt, self.receivedReadlineCallback)

    def checkWork(self):
        try:
            while self.channel.handle.GetNumberOfConsoleInputEvents() > 0:
                readline.callback_read_char()
                # self.receivedReadlineCallback(data) is called by
                # readline when appropriate
        except IOError, ioe:
            assert ioe.args[0] == errno.EAGAIN
            return 0
        except win32console.error:
            # stdin or stdout closed?
            self.cleanup()
            return 0
        worklength = self.lastdatalen
        self.lastdatalen = 0
        return worklength

    def receivedReadlineCallback(self, line):
        '''Call super-method, then re-install handler as this prints the prompt.'''
        self.lastdatalen += len(line)
        self.receivedCallback(line)
        self.do_prompt()


ReadlineWriter = _win32stdio._PollableWriteConsole


class ReadlineIO(stdio.StandardIO):
    '''A stdio.StandardIO alike that does not read or write input itself
    but delegates to readline.
    Aspires to work on Unix and Windows.
    '''

    def __init__(self, proto):
        """Fall back to StandardIO if readline is missing.
        Otherwise sneak in readline based members.
        """
        try:
            import readline
        except (ImportError, AttributeError):
            return stdio.StandardIO.__init__(self, proto)

        # adapted/simplified from the StandardIO __init__to use readline:
        # TODO: see is something essential got lost.
        from twisted.internet import reactor
        
        if sys.platform == 'win32':
            for stdfd in range(0, 1, 2):
                msvcrt.setmode(stdfd, os.O_BINARY)
            _pollingfile._PollingTimer.__init__(self, reactor)
            self.proto = proto
    
            # for now only create a ReadlineReader (TODO: check for
            # all the special cases in _win32stdio and _posixstdio)
            from twisted.internet import conio
            # sets self.dataReceived as linecallback for readline:
            self.stdin = ReadlineReader(conio.stdin, self.dataReceived,
                                        self.readConnectionLost)
            # currently the writer is not actually used:
            self.stdout = ReadlineWriter(conio.stdout, self.writeConnectionLost)
            # these are only necessary for a polling implementation:
            # need to be changed for posix and win32reactor
            self._addPollableResource(self.stdin)
            self._addPollableResource(self.stdout)
            self.proto.makeConnection(self)
        else:
            import sys
            sys.exit('TODO: implement ReadlineIO on Linux')
            # needed: a subclass of ProcessReader that does not actually read
            # but that calls readline instead.
            # (not sure about writing)

    # we need to override write methods to use readline prompting,
    # as writing through self.stdout does not update the console
    # state kept in readline:

    def write(self, data):
        self.stdin.do_prompt(prompt=data)
        #self.stdout.write(data)

    def writeSequence(self, seq):
        #self.stdout.write(''.join(seq))
        self.stdin.do_prompt(prompt=''.join(seq))


class ShellProtocol(basic.LineReceiver):
    '''Simple LineReceiver for interactive testing.'''

    delimiter = '\n' # does not work with '\r\n' on Windows...
                     # this might be an issue with the #2157 patches?

    def connectionMade(self):
        self.sendLine('connectionMade')

    def lineReceived(self, line):
        if line == 'quit':
            self.sendLine('OK quitting')
            self.transport.loseConnection()
            return
        self.sendLine('lineReceived %s' % line)

    def connectionLost(self, reason):
        # print 'connectionLost' # cannot print anymore (which is unexpected)
        reactor.stop()


if __name__ == '__main__':
    main()
