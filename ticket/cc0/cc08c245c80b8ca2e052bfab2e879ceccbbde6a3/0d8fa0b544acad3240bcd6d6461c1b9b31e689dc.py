#!/usr/bin/python

import os

remotePath = ':ext:buildmaster@192.168.62.233:/home/buildmaster/cvs'

os.system('cvs -d %s ls' % (remotePath))




