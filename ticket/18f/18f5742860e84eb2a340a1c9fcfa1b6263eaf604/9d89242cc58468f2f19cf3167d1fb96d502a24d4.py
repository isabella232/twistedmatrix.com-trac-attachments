#!/usr/bin/python

import os
from twisted.python.logfile import LogFile
from time import sleep
import threading

class LogFile_A(LogFile):
    def _openFile(self):
        """
        Open the log file, Delay before setting the original mask back
        """
        self.closed = False
        if os.path.exists(self.path):
            self._file = file(self.path, "r+", 1)
            self._file.seek(0, 2)
        else:
            if self.defaultMode is not None:
                # Set the lowest permissions
                oldUmask = os.umask(0777)
                print "Loaded Umask %s" % oldUmask
                try:
                    self._file = file(self.path, "w+", 1)
                finally:
                    sleep(1)
                    os.umask(oldUmask)
                    print "Restored Umask %s" % oldUmask
            else:
                self._file = file(self.path, "w+", 1)
        if self.defaultMode is not None:
            try:
                os.chmod(self.path, self.defaultMode)
            except OSError:
                # Probably /dev/null or something?
                pass


class LogFile_B(LogFile):
    def _openFile(self):
        """
        Open the log file, wait before proceeding
        """
        self.closed = False
        if os.path.exists(self.path):
            self._file = file(self.path, "r+", 1)
            self._file.seek(0, 2)
        else:
            if self.defaultMode is not None:
                # Set the lowest permissions
                oldUmask = os.umask(0777)
                print "Loaded Umask %s" % oldUmask
                sleep(1)
                try:
                    self._file = file(self.path, "w+", 1)
                finally:
                    os.umask(oldUmask)
                    print "Restored Umask %s" % oldUmask
            else:
                self._file = file(self.path, "w+", 1)
        if self.defaultMode is not None:
            try:
                os.chmod(self.path, self.defaultMode)
            except OSError:
                # Probably /dev/null or something?
                pass

def testFunc():
    l = LogFile_A('logfile1','/tmp')
    l.rotate()
    print "Completed Thread 1"

def testFunc2():
    l2 = LogFile_B('logfile','/tmp')
    l2.rotate()
    print "Completed Thread 2"

START_UMASK = os.umask(0)
print "Start Umask: %s" % START_UMASK
os.umask(START_UMASK)

t1 = threading.Thread(target=testFunc)
t1.start()
t2 = threading.Thread(target=testFunc2)
t2.start()
t1.join()
t2.join()

print "End Umask: %s" % os.umask(0)
