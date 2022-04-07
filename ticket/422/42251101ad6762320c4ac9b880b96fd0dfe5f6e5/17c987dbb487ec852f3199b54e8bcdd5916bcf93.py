# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
General helpers for L{twisted.web} unit tests.
"""

from cStringIO import StringIO

from twisted.internet.defer import succeed
from twisted.web import server
from twisted.trial.unittest import TestCase

def render(resource, request):
    written = StringIO()
    request.write = written.write
    result = resource.render(request)
    if isinstance(result, str):
        request.write(result)
        request.finish()
        return succeed(written.getvalue())
    elif result is server.NOT_DONE_YET:
        if request.finished:
            return succeed(written.getvalue())
        else:
            d = request.notifyFinish()
            d.addCallback(lambda _: written.getvalue())
	    return d
    else:
        raise ValueError("Unexpected return value: %r" % (result,))
