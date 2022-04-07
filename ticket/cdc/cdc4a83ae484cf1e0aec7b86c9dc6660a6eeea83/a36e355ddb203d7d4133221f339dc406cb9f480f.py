import sys
sys.argv = [sys.argv[0], "--reactor", "cf", "testcase.py"]

from twisted.trial.runner import TestLoader
TestLoader.modulePrefix = ''

from twisted.scripts.trial import run
run()
