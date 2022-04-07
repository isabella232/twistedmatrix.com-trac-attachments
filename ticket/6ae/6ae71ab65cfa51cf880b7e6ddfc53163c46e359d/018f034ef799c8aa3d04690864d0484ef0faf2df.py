'''
Provides do_the_monkeypatch_dance() which adds the GNU callback
API to the readline module.
On Unix ctypes is used.
On Windows monkey patching depends on a patched emacs.py in pyreadline
as posted to the IPython-devel list by Jorgen.

The rest of the module is for testing only.

:author: strank
'''

__docformat__ = "restructuredtext en"

import sys
import os
import time

import readline

if sys.platform == 'win32':
    import msvcrt
    from pyreadline.rlmain import rl
else:
    import ctypes
    from select import select


prompting = True
count = 0
maxlines = 10


def main():
    do_the_monkeypatch_dance()

    readline.callback_handler_install('Starting test, please do type:'
                                      + os.linesep, lineReceived)
    index = 0
    start = int(time.time())
    while prompting:
        # demonstrate that async stuff is possible:
        if start + index < time.time():
            if sys.platform == 'win32':
                rl.console.title("NON-BLOCKING: %d" % index)
            index += 1
        # busy waiting/polling on windows, select on Unix: (or use twisted)
        if sys.platform == 'win32':
            if msvcrt.kbhit():
                readline.callback_read_char()
        else:
            ready, _1, _2 = select([sys.stdin, ], [], [], 0.5)
            if ready:
                readline.callback_read_char()
    print "Done, index =", index


def lineReceived(line):
    global count, prompting
    count += 1
    print "Got line: %s" % line
    if count > maxlines:
        prompting = False
        readline.callback_handler_remove()
    else:
        readline.callback_handler_install('Got %s of %s, more typing please:'
                                          % (count, maxlines)
                                          + os.linesep, lineReceived)


def do_the_monkeypatch_dance():
    '''Monkeypatching that should actually be in different places:
    readline callback interface.
    '''
    import readline
    # define functions that should be part of readline:
    if sys.platform == 'win32':
        import pyreadline
        rlobject = pyreadline.rl
        rlobject.callback = None

        def callback_handler_install(self, prompt, callback):
            '''bool readline_callback_handler_install(string prompt, callback callback)
            Initializes the readline callback interface and terminal,
            prints the prompt and returns immediately
            '''
            self.callback = callback
            self.mode.readline_setup(prompt)

        def callback_handler_remove(self):
            '''Removes a previously installed callback handler
            and restores terminal settings
            '''
            self.callback = None

        def callback_read_char(self):
            '''Reads a character and informs the readline callback interface
            when a line is received
            '''
            if self.mode._readline_from_keyboard_poll():
                line = self.l_buffer.get_line_text() + '\n'
                self.console.write('\r\n') # this is the newline terminating input
                # however there is another newline added by
                # self.mode.readline_setup(prompt) called by callback_handler_install
                # this behaviour differs from GNU readline
                self.add_history(self.l_buffer.copy())
                self.callback(line)

        import new
        rlobject.callback_handler_install = new.instancemethod(
                callback_handler_install, rlobject, type(rlobject))
        rlobject.callback_handler_remove = new.instancemethod(
                callback_handler_remove, rlobject, type(rlobject))
        rlobject.callback_read_char = new.instancemethod(
                callback_read_char, rlobject, type(rlobject))

        readline.callback_handler_install = rlobject.callback_handler_install
        readline.callback_handler_remove = rlobject.callback_handler_remove
        readline.callback_read_char = rlobject.callback_read_char

    else:
        rl_lib = ctypes.cdll.LoadLibrary("libreadline.so.5")

        readline.callback_handler_remove = rl_lib.rl_callback_handler_remove
        readline.callback_read_char = rl_lib.rl_callback_read_char
        # the callback needs special treatment:
        rlcallbackfunctype = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_char_p)
        def setcallbackfunc(prompt, thefunc):
            rl_lib.rl_callback_handler_install(prompt, rlcallbackfunctype(thefunc))
        readline.callback_handler_install = setcallbackfunc


if __name__ == '__main__':
    main()
