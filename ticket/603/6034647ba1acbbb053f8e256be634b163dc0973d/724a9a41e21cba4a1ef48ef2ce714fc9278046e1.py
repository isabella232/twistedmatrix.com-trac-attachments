from socket import *

i = 1
while 1:
    server = socket(AF_INET, SOCK_STREAM)
    server.bind(('127.0.0.1', 0))
    server.listen(1)
    h, p = server.getsockname()
    if h != '127.0.0.1':
        print 'Wrong address! Expected 127.0.0.1, got %s. Port %s. Iteration #%s.' % (h, p, i)
        break
    server.close()
    i += 1

