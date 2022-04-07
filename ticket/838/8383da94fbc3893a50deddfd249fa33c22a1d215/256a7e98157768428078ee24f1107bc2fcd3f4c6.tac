from twisted.application import service, internet
from nevow import static, appserver

webroot = static.File('.')

application = service.Application('TestHttpAsynch')
svc = internet.TCPServer(8080, appserver.NevowSite(webroot))
svc.setServiceParent(application)

FIXME("""
        Create a large file before running this, then delete 
        these lines.
        """)
        
