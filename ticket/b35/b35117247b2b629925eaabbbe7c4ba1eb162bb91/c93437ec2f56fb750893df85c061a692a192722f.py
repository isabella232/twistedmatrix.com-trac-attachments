from __future__ import print_function

from itertools import count
import sys
import twisted

from twisted.internet.utils import getProcessValue as do
from twisted.internet.task import LoopingCall, react

counter = count()

def batch():
    print("Tick:", next(counter))
    for _ in range(80):
        do("/usr/bin/true")

def start(reactor):
    print("running twisted", twisted.version,
          "on python", sys.version)
    c = LoopingCall(batch)
    return c.start(1.0)

react(start, [])
