#!/usr/bin/python

import sys, os

filePath = sys.argv[1]
f = open(filePath, 'rU')

print 'Parsing: %s' % filePath

for r in f:
    line = r.lstrip(' ').rstrip('\n')
    start = line.find('test_')
    end = start + line[start:].find('.')
    path = line[:start].replace('.', os.path.sep)
    
    if end <= start:
        fname = line[start:]
    else:
        fname = line[start:end]

    fname += '.py'
    relpath = '%s%s' % (path, fname)
    
    print '\nModule: %s' % line
    
    if os.path.exists(relpath):
        abspath = os.path.abspath(relpath)
        print 'Relative path: %s' % relpath
        print 'Absolute path: %s' % abspath

        os.system('epydoc %s -v --simple-term' % abspath)
        
        print '-' * 100

        nxt = raw_input("Type 'y' to open this file or Enter to skip it: ")

        if nxt == 'y':
            os.system('open ' + abspath)
    else:
        print 'Error for %s' % relpath
        print '=' * 80
