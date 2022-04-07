''' 
Docstring copied from Python 2.5 to document what should be implemented:
"""
    This module provides mechanisms to use signal handlers in Python.
    
    Functions:
    
    signal(sig,action) -- set the action for a given signal (done)
    pause(sig) -- wait until a signal arrives [Unix only]
    alarm(seconds) -- cause SIGALRM after a specified time [Unix only]
    getsignal(sig) -- get the signal action for a given signal
    default_int_handler(action) -- default SIGINT handler (done, but acts string)
    
    Constants:
    
    SIG_DFL -- used to refer to the system default handler
    SIG_IGN -- used to ignore the signal
    NSIG -- number of defined signals
    
    SIGINT, SIGTERM, etc. -- signal numbers
    
    *** IMPORTANT NOTICE ***
    A signal handler function is called with two arguments:
    the first is the signal number, the second is the interrupted stack frame.
"""
*** According to http://java.sun.com/products/jdk/faq/faq-sun-packages.html
'writing java programs that rely on sun.* is risky: they are not portable, and are not supported.'

This module depends on sun.misc.Signal* so this will likely not make it into jython proper.
'''
import sun.misc.Signal
import sun.misc.SignalHandler
import threading
import exceptions

#import java 

import traceback
from StringIO import StringIO
debug = 0

SIGHUP    = 1
SIGINT    = 2
SIGQUIT   = 3
SIGILL    = 4
SIGTRAP   = 5
SIGABRT   = 6
SIGPOLL   = 7
SIGFPE    = 8
SIGKILL   = 9
SIGBUS    = 10
SIGSEGV   = 11
SIGSYS    = 12
SIGPIPE   = 13
SIGALRM   = 14
SIGTERM   = 15
SIGURG    = 16
SIGSTOP   = 17
SIGTSTP   = 18
SIGCONT   = 19
SIGCHLD   = 20
SIGTTIN   = 21
SIGTTOU   = 22
SIGXCPU   = 24
SIGXFSZ   = 25
SIGVTALRM = 26
SIGPROF   = 27
SIGWINCH  = 28
SIGINFO   = 29
SIGUSR1   = 30
SIGUSR2   = 31

SIG_DFL = sun.misc.SignalHandler.SIG_DFL # default system handler
SIG_IGN = sun.misc.SignalHandler.SIG_IGN # handler to ignore a signal

NSIG = 32 # number of defined signals

_signals = {
    2: sun.misc.Signal('INT'),
    3: sun.misc.Signal('QUIT'),
    4: sun.misc.Signal('ILL'),
    5: sun.misc.Signal('TRAP'),
    6: sun.misc.Signal('ABRT'),
    # 7: sun.misc.Signal('EMT'),
    8: sun.misc.Signal('FPE'),
    9: sun.misc.Signal('KILL'),
    10: sun.misc.Signal('BUS'),
    11: sun.misc.Signal('SEGV'),
    12: sun.misc.Signal('SYS'),
    13: sun.misc.Signal('PIPE'),
    14: sun.misc.Signal('ALRM'),
    15: sun.misc.Signal('TERM'),
    16: sun.misc.Signal('URG'),
    17: sun.misc.Signal('STOP'),
    18: sun.misc.Signal('TSTP'),
    19: sun.misc.Signal('CONT'),
    20: sun.misc.Signal('CHLD'),
    21: sun.misc.Signal('TTIN'),
    22: sun.misc.Signal('TTOU'),
    23: sun.misc.Signal('IO'),
    24: sun.misc.Signal('XCPU'),
    25: sun.misc.Signal('XFSZ'),
    26: sun.misc.Signal('VTALRM'),
    27: sun.misc.Signal('PROF'),
    28: sun.misc.Signal('WINCH'),
    # 29: sun.misc.Signal('INFO'),
    30: sun.misc.Signal('USR1'),
    31: sun.misc.Signal('USR2')
}

class JythonSignalHandler(sun.misc.SignalHandler):
    def __init__(self,signal,action):
        if debug: print 'JythonSignalHandler initing with action', str(action),'for', signal.getName()
        self.action = action
        self.signal = signal
        self.oldHandler = sun.misc.Signal.handle(self.signal,self)
    def handle(self, signal):
        if debug: print 'Diagnostic Signal Handler called for signal:',signal.getName(),':',signal.getNumber()
        if self.signal==signal:
            if hasattr(self.action,'class') and self.action.getClass() ==  sun.misc.NativeSignalHandler:
                pass #NativeSignal Handlers are called by the JVM not us
            else:
                self.action()
        if self.oldHandler:
            self.oldHandler.handle(signal)

def signal(sig, action):
    """
    signal(sig, action) -> action

    Set the action for the given signal.  The action can be SIG_DFL,
    SIG_IGN, or a callable Python object.  The previous action is
    returned.  See getsignal() for possible return values.

    *** IMPORTANT NOTICE ***
    A signal handler function is called with two arguments:
    the first is the signal number, the second is the interrupted stack frame.
    """
    if debug: print 'signal called with ',sig,action
    signal = _signals[sig]
    newHandler = JythonSignalHandler(signal,action)
    oldHandler = newHandler.oldHandler
    return oldHandler

def getsignal(name):
    """
    crappy
    """
    return SIG_DFL

def default_int_handler(*args):
    """
    default_int_handler(...)
    
    The default handler for SIGINT installed by Python.
    It raises KeyboardInterrupt.
    """
    raise exceptions.KeyboardInterrupt
