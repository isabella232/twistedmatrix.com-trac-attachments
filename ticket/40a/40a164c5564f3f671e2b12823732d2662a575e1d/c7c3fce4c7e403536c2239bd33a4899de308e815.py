def application(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    details = ("SERVER_NAME: %(SERVER_NAME)s\n"
               "SERVER_PORT: %(SERVER_PORT)s\n" % environ)
    return [details.encode('ascii')]
