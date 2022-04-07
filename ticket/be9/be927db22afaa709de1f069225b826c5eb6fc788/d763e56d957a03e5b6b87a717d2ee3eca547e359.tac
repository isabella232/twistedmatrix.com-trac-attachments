from twisted.application.service import Application
from twisted.python.log import startLogging

application = Application("Broken logging")
startLogging(file('minimal-broken.log', 'w'))
