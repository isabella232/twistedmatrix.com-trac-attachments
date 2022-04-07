from qt import *

class TestApplication(QApplication):
    def connected(self, perspective):
        ##this doesnt work:
        mW = QMainWindow()
        self.setMainWidget(mW)
        mW.show()
        
        ##this does work:
##        self.mW = QMainWindow()
##        self.setMainWidget(self.mW)
##        self.mW.show()


if __name__ == '__main__':
    
    q = TestApplication([])
    from twisted.internet import qtreactor
    r = qtreactor.install(q)
    
    
    from twisted.spread import pb
    from twisted.cred import credentials
    factory = pb.PBClientFactory()
    r.connectTCP("localhost", 8800, factory)
    def1 = factory.login(credentials.UsernamePassword("admin","change"))
    def1.addCallback(q.connected)
    r.run()
