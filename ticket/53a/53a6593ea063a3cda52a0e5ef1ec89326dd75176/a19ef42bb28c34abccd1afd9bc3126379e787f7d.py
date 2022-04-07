#!/usr/bin/python
# export PYTHONPATH=/local/twisted-svn/lib/python2.3/site-packages
# twistd -y ./DAVservice.py

##############
# Config
##############

# SSL settings
sslCertKey = "ssl/hostcert.pem"
sslPrivateKey = "ssl/hostkey.pem"

# DAV settings
davrootdir = "/"

# service settings
serviceName = "DAVservice"
transport = "tcp"
#transport = "ssl"
port = 8901
#interface = "127.0.0.1"
interface = None

def serviceDescription():
    if transport is not None and port is not None:
        str = transport+":"+repr(port)
    elif transport is None:
        raise Exception("Service transport undefined")
    else:
        raise Exception("Service port undefined")
    if interface is not None:
        str += ":interface="+interface
    if transport=="ssl":
        if sslPrivateKey is not None:
            str += ":privateKey="+sslPrivateKey
        else:
            raise Exception("SSL private key not configured")
        if sslCertKey is not None:
            str += ":certKey="+sslCertKey
    return str

###############
# DAV server
###############

# auth realm
from twisted.cred import portal
from zope.interface import Interface, implements

class IDAVUser(Interface):
    pass

class DAVUser(object):
    implements(IDAVUser)

class DAVAuthRealm(object):
    implements(portal.IRealm)

    def requestAvatar(self, avatarId, mind, *interfaces):
        if IDAVUser in interfaces:
            return IDAVUser, DAVUser()

        raise NotImplementedError("Only IDAVUser interface is supported")

davportal=portal.Portal(DAVAuthRealm())

from twisted.cred import checkers
davchecker=checkers.InMemoryUsernamePasswordDatabaseDontUse(guest='guest123')

from twisted.web2.dav import static
davroot=static.DAVFile(davrootdir)

from twisted.web2.auth import wrapper
from twisted.web2.auth import basic
davportal.registerChecker(davchecker)
root = wrapper.HTTPAuthResource(davroot,
                                (
                                 basic.BasicCredentialFactory("My realm"),
                                ),
                                davportal,
                                (IDAVUser,))

from twisted.web2 import server
site = server.Site(root)

from twisted.application import service, strports
from twisted.web2 import channel
application = service.Application(serviceName)
DAVservice = strports.service(serviceDescription(),
                              channel.HTTPFactory(site))
DAVservice.setServiceParent(application)
