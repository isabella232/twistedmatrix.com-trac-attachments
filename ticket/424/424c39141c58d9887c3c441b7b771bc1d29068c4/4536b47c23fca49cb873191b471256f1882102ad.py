#!/usr/bin/python

import pyexpat

def onStartElement(name, attrs):
	qname_bad  = name.split(" ")
	qname_good = name.rsplit(" ", 1)
	attrs_bad  = dict()
	attrs_good = dict()
        for k, v in attrs.items():
		if k.find(" ") != -1:
			aqname = k.split(" ")
			attrs_bad [(aqname[0], aqname[1])] = v
			aqname = k.rsplit(" ", 1)
			attrs_good[(aqname[0], aqname[1])] = v
			del attrs[k]
	print "BAD: \n----\n%s\n%s\n" % (qname_bad,  attrs_bad)
	print "GOOD:\n----\n%s\n%s\n" % (qname_good, attrs_good)

parser = pyexpat.ParserCreate("UTF-8", " ")
parser.StartElementHandler = onStartElement

xml = """<?xml version="1.0"?>
		<root xmlns="some weird namespace "
		      xmlns:a="another weird namespace"
		      a:foo='bar'
		/>
"""

parser.Parse(xml)
