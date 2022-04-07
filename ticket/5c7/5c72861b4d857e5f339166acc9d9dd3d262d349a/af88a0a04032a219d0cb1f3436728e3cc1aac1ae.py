#!/usr/bin/python2.7

import traceback
import twisted
from twisted.python import failure


try:
    raise Exception(u'\u16c3')
except Exception:
    print "Native traceback:"
    traceback.print_exc()

print

try:
    raise Exception(u'\u16c3')
except Exception:
    f = failure.Failure()

print "Twisted", twisted.__version__, "Failure traceback:"
print f.getBriefTraceback()
