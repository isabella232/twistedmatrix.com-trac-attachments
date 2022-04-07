#!/usr/bin/env python

import sys
import time
import cProfile
import pstats

from twisted.words.xish import domish

class XmlParser(object):
    def __init__(self):
        self._reset()
    
    def parse(self, buf):
        self.stream.parse(buf)
        return self.entity
    
    def serialize(self, obj):
        if isinstance(obj, domish.Element):
            obj = obj.toXml()
            return obj
    
    def onDocumentStart(self, rootelem):
        self.entity = rootelem
    
    def onElement(self, element):
        if isinstance(element, domish.Element):
            self.entity.addChild(element)
        else:
            pass
    
    def _reset(self):
        # Setup the parser
        self.stream = domish.elementStream()
        self.stream.DocumentStartEvent = self.onDocumentStart
        self.stream.ElementEvent = self.onElement
        self.stream.DocumentEndEvent = self.onDocumentEnd
        self.entity = None
    
    def onDocumentEnd(self):
        pass

def slowfunc(elements):
    for e in elements:
	e.toXml()

if __name__ == '__main__':
    # read in and parse all xml from stdin

    elements = []

    for line in sys.stdin.xreadlines():
	p = XmlParser()
	elem = p.parse(line)

	elements.append(elem)

    print "Read %d elements from the log." % (len(elements),)

    start = time.time()
    cProfile.run('slowfunc(elements)', 'profile.data')
    end = time.time()

    print "Serialized %d elements in %0.2f seconds." % (len(elements), 
							end - start)

    p = pstats.Stats('profile.data')
    p.strip_dirs().sort_stats('time').print_stats(10)
