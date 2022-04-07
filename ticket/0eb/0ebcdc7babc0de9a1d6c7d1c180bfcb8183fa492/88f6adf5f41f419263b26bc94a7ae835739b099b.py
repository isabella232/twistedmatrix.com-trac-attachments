#!/usr/bin/env python2.5
# -*- coding: iso-8859-2 -*-

'''Skeleton of a streaming XMLRPC server

Just for test:

  # start the server:
  $ twistd -noy stream_err.py

  # send a request (different shell):
  $ python stream_err.py

What I get here: the buffer works, but waits indefinitly for a last 'read'
 - if I press ^C at the server shell, it finishes off the response, which 
 is complete!
I even tried to experiment with the IByteStream's length - I don't really
understand how it affects read-ing - see line 417.
'''

##
## async xmlrpclib
##
import xmlrpclib, types

#print xmlrpclib.Marshaller
Marshaller = (xmlrpclib.Marshaller if not xmlrpclib.FastMarshaller 
    else xmlrpclib.FastMarshaller)
FastMarshaller = Marshaller
Fault = xmlrpclib.Fault

ENCODING = 'utf8'

class AsyncMarshaller(Marshaller):
  '''asyncron marshaller

  calls write for every chuk of output'''
  dispatch = Marshaller.dispatch
  def __init__(self, *args, **kwds):
    write = kwds.get('write', None)
    del kwds['write']
    Marshaller.__init__(self, *args, **kwds)
    if callable(write): self._write = write
    else: self._write = None
 
  def dumps(self, values):
    '''dumps value'''
    if self._write is None:
      out = []
      write = out.append
    else: 
      out = None
      write = self._write
    dump = self.__dump
    if isinstance(values, Fault):
      # fault instance
      write("<fault>\n")
      dump({'faultCode': values.faultCode,
         'faultString': values.faultString},
         write)
      write("</fault>\n")
    else:
      write("<params>\n")
      for v in values:
        write("<param>\n")
        dump(v, write)
        write("</param>\n")
      write("</params>\n")
    #
    if out is not None:
      result = ''.join(out)
      del out
    else:
      result = ''
    return result
    
  def __dump(self, value, write):
    '''dump dispatcher

    dispatches according to type of value'''
    try:
      f = self.dispatch[type(value)]
    except KeyError:
      raise TypeError, "cannot marshal %s objects" % type(value)
    else:
      f(self, value, write)

  def dump_generator(self, value, write):
    '''dump for generator types
    
    same as dump_list or dump_dict, but works on generators
    (iterable types)'''
    dump = self.__dump
    if hasattr(value, 'iteritems'):
      write('<value><struct>')
      for key, val in value.iteritems():
        write('<member><name>')
        dump(key, write)
        write('</name>')
        dump(val, write)
        write('</member>')
      #
      write('</struct></value>')

    else:
      write('<value><array><data>')
      for val in value: 
        dump(val, write)
      write('</data></array></value>')
  #
  dispatch[types.GeneratorType] = dump_generator

##
# Convert a Python tuple or a Fault instance to an XML-RPC packet.
#
# @def dumps(params, **options)
# @param params A tuple or Fault instance.
# @keyparam methodname If given, create a methodCall request for
#     this method name.
# @keyparam methodresponse If given, create a methodResponse packet.
#     If used with a tuple, the tuple must be a singleton (that is,
#     it must contain exactly one element).
# @keyparam encoding The packet encoding.
# @return A string containing marshalled data.

def dumps(params, methodname=None, methodresponse=None, encoding=None,
     allow_none=0, write=None):
  """data [,options] -> marshalled data

  Convert an argument tuple or a Fault instance to an XML-RPC
  request (or response, if the methodresponse option is used).

  In addition to the data object, the following options can be given
  as keyword arguments:

    methodname: the method name for a methodCall packet

    methodresponse: true to create a methodResponse packet.
    If this option is used with a tuple, the tuple must be
    a singleton (i.e. it can contain only one element).

    encoding: the packet encoding (default is UTF-8)

    allow_none: if true, allows None as value (discrepancy according 
    to the XM-RPC standard)

    write: method called for output - if None, then back to the
    old behaviour (dumps into a string, and return that).

  All 8-bit strings in the data structure are assumed to use the
  packet encoding. Unicode strings are automatically converted,
  where necessary.
  """

  assert isinstance(params, types.TupleType) or isinstance(params, Fault),\
      "argument must be tuple or Fault instance"

  if isinstance(params, Fault):
    methodresponse = 1
  elif methodresponse and isinstance(params, types.TupleType):
    assert len(params) == 1, "response tuple must be a singleton"

  if not encoding:
    encoding = "utf-8"

  m = AsyncMarshaller(encoding, allow_none, write=write)

  if encoding != "utf-8":
    xmlheader = "<?xml version='1.0' encoding='%s'?>\n" % str(encoding)
  else:
    xmlheader = "<?xml version='1.0'?>\n" # utf-8 is default

  # standard XML-RPC wrappings
  if methodname:
    # a method call
    if not isinstance(methodname, types.StringType):
      methodname = methodname.encode(encoding)
    data = ((
      xmlheader,
      "<methodCall>\n"
      "<methodName>", methodname, "</methodName>\n",)
      ("</methodCall>\n",)
      )
  elif methodresponse:
    # a method response, or a fault structure
    data = ((
      xmlheader,
      "<methodResponse>\n"),
      ("</methodResponse>\n",)
      )
  else:
    return (('',), ('',)) # return as is
  if write is None:
    result = (''.join(data[0]), m.dumps(params),
        ''.join(data[-1]))
  else:
    result = ''
    write(''.join(data[0]))
    m.dumps(params)
    write(''.join(data[-1]))
  return ''.join(result)

#xmlrpclib.Marshaller = AsyncMarshaller
#xmlrpclib.dumps = dumps

import itertools, functools, string, shelve, tempfile, os, pprint
from datetime import datetime
import time
from twisted.internet import defer, threads

def enc(obj, encoding=ENCODING):
  if isinstance(obj, unicode): return obj.encode(encoding)
  else: return str(obj)


def flatten_list(alist):
  for elt in alist:
    if isinstance(elt, (tuple, list)):
      for x in elt:
        yield x
    else:
      yield elt

def print_err(failure):
  if hasattr(failure, 'printTraceback'): failure.printTraceback()
  else: print pprint.pformat(failure)

TEMPFILES = []
def tempfilename(*args, **kwds):
  (fdesc, fname) = tempfile.mkstemp(*args, **kwds)
  os.close(fdesc)
  os.unlink(fname)
  TEMPFILES.append(fname)
  return fname

def del_tempfiles():
  for fn in TEMPFILES:
    if os.path.exists(fn):
      try:
        os.unlink(fn)
      except:
        pass
import atexit
atexit.register(del_tempfiles)

from twisted.web2 import stream

##
## XMLRPC server
##

import sys
from twisted.web2 import server, http, resource, channel, xmlrpc
from twisted.web2 import static, http_headers, responsecode, stream
MimeType = http_headers.MimeType

import threading, thread

class StringCache(object):
  '''Queue for a string

  buffers everything onto disk, and gives back chunk sized parts of it'''
  def __init__(self, chunksize=1*1024**2):
    self._dbfn = tempfile.mkdtemp()
    self.chunksize = chunksize
    self._lock = threading.Lock()
    self.truncate()
    self.buffer = []
    self.length = 0
    self._blen = 0
    self._first = 0
    self._last = 0

  def lock(self, txt=''):
    '''locking mechanism

    against nasty threads'''
    if not self._lock.acquire(False):
      print 'BLOCKING!'
      self._lock.acquire(True)

  def release(self, txt=''):
    '''release lock'''
    self._lock.release()

  def _write(self, key, data):
    '''writes to disk'''
    fn = os.path.join(self._dbfn, str(key))
    msk = os.umask(0066)
    fh = open(fn, 'wb')
    os.umask(msk)
    fh.truncate()
    fh.seek(0,0)
    print 'writing %d to %s'%(len(data), fn)
    fh.write(data)
    fh.flush()
    fh.close()

  def _read(self, key):
    '''reads back from disk'''
    fn = os.path.join(self._dbfn, str(key))
    fh = open(fn, 'rb')
    data = fh.read()
    print 'read %d from %s'%(len(data), fn)
    fh.seek(0, 2)
    length = fh.tell()
    if len(data) != length: print '!!!', len(data), length, '!!!'
    fh.close()
    os.unlink(fn)
    return data

  def put(self, text):
    '''puts the given text to the end'''
    if text is not None:
      self.lock('PUT')
      self.buffer.append(text)
      n = len(text)
      self._blen += n 
      self.length += n
      if self._blen >= self.chunksize or len(self.buffer) > 32766:
        nxt = str(self._last)
        try:
          self._write(nxt, ''.join(self.buffer))
        except Exception, dbme:
          dt = ''.join(self.buffer)
          pprint.pprint(( nxt, type(dt), len(dt), dbme))
          raise dbme
        self._last += 1
        self.buffer = []
        self._blen = 0
      self.release()

  def get(self):
    '''gets the first chunk'''
    res = None
    self.lock('GET')
    b = bool(self.buffer)
    if self._first < self._last:
      key = str(self._first)
      res = self._read(key)
      self._first += 1
    elif self.buffer:
      b = False
      res = ''.join(self.buffer)
      self.buffer = []
      self._blen = 0
    if res is not None:
      self.length -= len(res)
      if b: 
        print 'LEFT in bufferben!', self._blen, sum(map(len, self.buffer))
    self.release()
    return res

  def truncate(self):
    '''truncactes the cache'''
    self.lock('TRUNC')
    self.buffer = []
    self._blen = 0
    self.length = 0
    for fn in (os.path.join(self._dbfn, fn) 
        for fn in os.listdir(self._dbfn)):
      os.unlink(fn)
    #
    self._first = 0
    self._last = 0
    self.release()
    print '.'

  def __del__(self):
    '''delete every file and folder'''
    if hasattr(self, 'db') and self.db:
      try:
        self.db.close()
      except:
        pass
      self.db = None
    if self._dbfn and os.path.exists(self._dbfn):
      if os.path.isdir(self._dbfn):
        try:
          for fn in (os.path.join(self._dbfn, fn) 
              for fn in os.listdir(self._dbfn)):
            os.unlink(fn)
        except:
          pass
      try:
        os.unlink(self._dbfn)
      except:
        pass

from zope.interface import implements

class XMLRPCRenderStream(object):
  '''IByteStrem which produces what consumed by write
  
  Maybe the dumps call should be separated from here...
  '''

  implements(stream.IByteStream)

  def __init__(self, src):
    self.src = src
    self.closed = False
    self.cache = StringCache()
    self.waiting = []
    if isinstance(src, defer.Deferred):
      self.dfr = self.src.addCallback(dumps, methodresponse=1,
          allow_none=1, write=self.write)
    else:
      self.dfr = threads.deferToThread(dumps, 
          src, methodresponse=1, write=self.write)
    #
    self.dfr.addErrback(print_err)
    self.dfr.addCallback(self.finish)

  def _getlength(self):
    '''returns the length of the stream (as far as we know)'''
    # this gives back no response (0 bytes):
    # return (None if self.cache.length != 0 else 0)
    # this seems to work:
    return self.cache.length
  length = property(_getlength)

  def write(self, data):
    '''consumes data'''
    if data:
      if not self.closed:
        self.cache.put(data)
        self._flush()
      else:
        raise StopIteration, 'write to a closed stream!'

  def _flush(self):
    '''produces into waiting 'read' calls, if any'''
    while self.waiting and self.length > 0:
      dfr = self.waiting.pop(0)
      buf = []
      while 1:
        data = self.cache.get()
        if data is None: 
          break
        buf.append(data)
      data = ''.join(buf)
      dfr.callback(data)

  def read(self):
    '''returns a Deferred for the read data'''
    if not self.closed or self.cache.length > 0:
      res = defer.Deferred()
      self.waiting.append(res)
      if self.closed:
        self._flush()
    else:
      res = None
    return res

  def close(self):
    '''reader closes this stream'''
    print 'CLOSE', self.length, self.cache.length
    self._flush()
    self.cache.truncate()

  def finish(self, *args):
    '''writer closes this stream'''
    #print 'FINISH', self.cache.length
    self._flush()
    while self.waiting:
      self.waiting.pop(0).callback(None)
    self.closed = True

  def split(self, point):
    return stream.fallbackSplit(self, point)

class XMLRPCInterface(xmlrpc.XMLRPC):
  '''the XML-RPC server'''
  def __init__(self, functions=[]):
    xmlrpc.XMLRPC.__init__(self)
    self.functions = [self.generateData] + functions

  def getFunction(self, functionPath):
    '''Given a string, return a function, or raise NoSuchFunction.

    This returned function will be called, and should return the result 
    of the call, a Deferred, or a Fault instance.
      Override in subclasses if you want your own policy. The default
    policy is that given functionPath 'foo', return the method at 
    self.xmlrpc_foo, i.e. getattr(self, "xmlrpc_" + functionPath). 
    If functionPath contains self.separator, the sub-handler for the 
    initial prefix is used to search for the remaining path.'''
    if len(self.functions) == 1:
      fun = self.functions[0]
    else:
      fun = dict((f.__name__, f) 
          for f in self.functions).get(functionPath, None)
    if fun:
      return fun
    else:
      raise xmlrpc.NoSuchFunction(self.NOT_FOUND, 
          'No such function %s'%functionPath)

  def _cbRender(self, result, request):
    if not isinstance(result, Fault):
      result = (result,)
    try:
      s = XMLRPCRenderStream(result)
    except Exception, e:
      f = Fault(self.FAILURE, "can't serialize output (%s)"%e)
      print '_cbRender error:', e
      s = xmlrpclib.dumps(f, methodresponse=1)
    return http.Response(responsecode.OK, 
      {'content-type': http_headers.MimeType('text', 'xml')},
      s)

  def _listFunctions(self):
    return self.functions

  def generateData(self, ctx, length=1000):
    if not length: length = 1000
    adict = {'ctx': map(str, dir(ctx)), 'local': map(str, locals())}
    return ((i, adict) for i in xrange(0, length))

##
## Toplevel
##

class Toplevel(resource.Resource):
  addSlash = True
  child_test = XMLRPCInterface()

  def render(self, ctx):
    return http.Response(
      200, 
      {'content-type': http_headers.MimeType('text', 'html')},
      """<html><body>
      <a href="dealer">dealer_portal</a><br>
      </body></html>""")

site = server.Site(Toplevel())

PORT = 8082

# Standard twisted application Boilerplate
from twisted.application import service, strports
application = service.Application("xmlrpc_interface")
s = strports.service('tcp:%d'%PORT, channel.HTTPFactory(site))
s.setServiceParent(application)

if __name__ == '__main__':
  #client
  import xmlrpclib
  server = xmlrpclib.ServerProxy('http://localhost:%d/test'%PORT, 
    verbose=1, allow_none=1)
  print server
  print server.test(int(sys.argv[1]) if len(sys.argv) > 1 else None)


# vim: fenc=iso-8859-2 fileformat=unix:
