import time
import SimpleHTTPServer
import SocketServer


class Handler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        for i in range(20):
            self.wfile.write('line %d\r\n' % i)
            time.sleep(0.1)


class Server(SocketServer.TCPServer):
    allow_reuse_address = True


httpd = Server(('', 8000), Handler)
httpd.serve_forever()
