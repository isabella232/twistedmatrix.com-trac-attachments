import cherrypy

def application(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    details = ("SERVER_NAME: %(SERVER_NAME)s\n"
               "SERVER_PORT: %(SERVER_PORT)s\n" % environ)
    return [details.encode('ascii')]


# Mount the WSGI callable object (app) on the root directory
cherrypy.tree.graft(application, '/')

# Set the configuration of the web server
cherrypy.config.update({
    'engine.autoreload_on': True,
    'log.screen': True,
    'server.socket_file': '/tmp/sock'
})

# Start the CherryPy WSGI web server
cherrypy.engine.start()
cherrypy.engine.block()
