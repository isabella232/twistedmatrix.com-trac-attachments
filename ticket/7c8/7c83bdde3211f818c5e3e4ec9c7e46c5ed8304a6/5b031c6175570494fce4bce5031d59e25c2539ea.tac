from twisted.application.service import Application

from twisted.runner.procmon import ProcessMonitor

application = Application("procmontest")
monitor = ProcessMonitor()
monitor.setServiceParent(application)

monitor.addProcess(
        "kittens",
        ["/usr/bin/python", "-c",
        "import os; print os.getuid(), os.geteuid()"],
        uid=1000, gid=1000)
