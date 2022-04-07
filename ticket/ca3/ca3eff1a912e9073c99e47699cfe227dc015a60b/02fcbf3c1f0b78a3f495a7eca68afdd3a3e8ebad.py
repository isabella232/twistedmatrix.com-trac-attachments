from twisted.web import http

class MyRequestHandler(http.Request):
    def process(self):
        self.write(u'Hello world!\n')
        self.finish()

class MyHttp(http.HTTPChannel):
    requestFactory = MyRequestHandler

class MyHttpFactory(http.HTTPFactory):
    protocol = MyHttp

if __name__ == "__main__":
    from twisted.internet import reactor
    reactor.listenTCP(8000, MyHttpFactory())
    reactor.run()
