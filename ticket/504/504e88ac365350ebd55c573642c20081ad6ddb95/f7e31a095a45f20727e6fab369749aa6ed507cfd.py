#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf8

import sys
from traceback import print_exc

def gen():
    yield 1
    raise ValueError, "this is an error"


if __name__ == "__main__":

    print "Normal traceback:"
    g = gen()
    g.next()
    try:
        g.send(None)
    except:
        print_exc()
    
    print
    print "Rethrown traceback:"
    g = gen()
    g.next()
    try:
        g.send(None)
    except:
        try:
            g.throw(*sys.exc_info())
        except:
            print_exc()

