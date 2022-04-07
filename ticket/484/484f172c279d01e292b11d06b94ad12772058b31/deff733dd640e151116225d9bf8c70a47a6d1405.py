"""Twisted integration with SQLAlchemy.

$Id$

THIS SOFTWARE IS UNDER MIT LICENSE.
Copyright (c) 2006 Perillo Manlio (manlio.perillo@gmail.com)

Read LICENSE file for more informations.
"""


from twisted.internet import defer, threads
from twisted.python import log

from sqlalchemy.engine import base, default, strategies, threadlocal, url
from sqlalchemy import util, schema, exceptions, pool as poollib



class Pool(poollib.SingletonThreadPool):
    """A custom pool for Twisted.
    """

    def __init__(self, creator, pool_size=5, noisy=True, **kwargs):
        poollib.SingletonThreadPool.__init__(self, creator, pool_size,
                                             **kwargs)
        
        self.noisy = noisy

    # Let's use Twisted logging system
    def log(self, msg):
        if self.noisy:
            log.msg(msg)

 
class EngineStrategy(strategies.DefaultEngineStrategy):
    """A custom engine strategy for Twisted.
    """

    def __init__(self):
        strategies.DefaultEngineStrategy.__init__(self, 'twisted')


    def create(self, name_or_url, **kwargs):
        # create url.URL object
        u = url.make_url(name_or_url)
        
        # get module from sqlalchemy.databases
        module = u.get_module()

        dialect_args = {}
        # consume dialect arguments from kwargs
        for k in util.get_cls_kwargs(module.dialect):
            if k in kwargs:
                dialect_args[k] = kwargs.pop(k)
                
        # create dialect
        dialect = module.dialect(**dialect_args)

        # assemble connection arguments
        (cargs, cparams) = dialect.create_connect_args(u)
        cparams.update(kwargs.pop('connect_args', {}))

        # create a new pool
        dbapi = kwargs.pop('module', dialect.dbapi())
        if dbapi is None:
            raise exceptions.InvalidRequestError("Cant get DBAPI module for dialect '%s'" % dialect)

        def creator():
            try:
                conn = dbapi.connect(*cargs, **cparams)
                if global_connect:
                    import sqlalchemy

                    # Make sure that the engine is connected to the
                    # global metadata for every thread
                    sqlalchemy.global_connect(engine)

                if openfun is not None:
                    openfun(conn)
                    
                return conn
            except Exception, e:
                raise exceptions.DBAPIError("Connection failed", e)

        pool_args = {}
        # consume pool arguments from kwargs
        openfun = kwargs.pop("openfun", None)
        global_connect = kwargs.pop("global_connect", False)
        pool_cls_kwargs = util.get_cls_kwargs(Pool)
        pool_cls_kwargs.remove("use_threadlocal") # not used
        pool_cls_kwargs.remove("echo") # not used
        for k in pool_cls_kwargs:
            if k in kwargs:
                pool_args[k] = kwargs.pop(k)

        pool = Pool(creator, **pool_args)
        
        provider = self.get_pool_provider(pool)

        # create engine
        engineclass = self.get_engine_cls()
        engine_args = {}
        for k in util.get_cls_kwargs(engineclass):
            if k in kwargs:
                engine_args[k] = kwargs.pop(k)
                
        # all kwargs should be consumed
        if len(kwargs):
            raise TypeError(
                "Invalid argument(s) %s sent to create_engine(), using configuration %s/%s/%s.  Please check that the keyword arguments are appropriate for this combination of components." % (','.join(["'%s'" % k for k in kwargs]), dialect.__class__.__name__, pool.__class__.__name__, engineclass.__name__)
            )

        engine = engineclass(provider, dialect, **engine_args)
        return engine

    def pool_threadlocal(self):
        return True

    def get_pool_provider(self, pool):
        return threadlocal.TLocalConnectionProvider(pool)

    def get_engine_cls(self):
        return threadlocal.TLEngine



class Engine:
    """I represent a wrapper to a SQLAlchemy engine, with support for
    asyncronous queries.

    This class implements the Connectable interface, so it can be
    bound to a metadata.
    """

    engineURL = None # the URL describing the engine to use
    engineName = None # the name of the engine used

    noisy = True # if true, generate informational log messages
    pool_size = 10 # the number of connections in pool
    name = None # Name to assign to thread pool for debugging (XXX is this used?)
    openfun = None # A function to call on new connections

    running = False # true when the pool is operating


    def __init__(self, url, **kwargs):
        """Create a new Engine.
        """

        self.urlURL = url
        self.engineName = url[:url.find(':')]
        self.kwargs = kwargs

        kwargs.pop("use_threadlocal", None) # unused
        name = kwargs.pop("name", self.name) # remove from here

        # Create the internal engine
        strategy = EngineStrategy()
        self._engine = strategy.create(url, **kwargs)

        # Setup a dedicated thread pool
        from twisted.python import threadpool
        from twisted.internet import reactor

        pool_size = kwargs.get("pool_size", self.pool_size)
        self.threadpool = threadpool.ThreadPool(1, pool_size, name)
        self.startID = reactor.callWhenRunning(self._start)


    def _start(self):
        self.startID = None
        return self.start()

    def start(self):
        """Start the thread pool.

        If you are using the reactor normally, this function does *not*
        need to be called.
        """

        if not self.running:
            from twisted.internet import reactor

            self.threadpool.start()
            self.shutdownID = reactor.addSystemEventTrigger(
                'during', 'shutdown', self.finalClose
                )
            self.running = True

    def close(self):
        """Close all pool connections and shutdown the pool."""

        from twisted.internet import reactor

        if self.shutdownID:
            reactor.removeSystemEventTrigger(self.shutdownID)
            self.shutdownID = None
        if self.startID:
            reactor.removeSystemEventTrigger(self.startID)
            self.startID = None

        self.finalClose()

    def finalClose(self):
        """This should only be called by the shutdown trigger."""

        self.shutdownID = None
        self._engine.dispose()
        self.threadpool.stop()
        self.running = False


    # XXX check me
    def __getstate__(self):
        return {
            'engineRRL': self.engineURL,
            'kwargs': self.kwargs
            }

    def __setstate__(self, state):
        self.__dict__ = state
        self.__init__(self.engineURL, **self.kwargs)


    def globalConnect(self):
        import sqlalchemy

        sqlalchemy.global_connect(self._engine)

    def boundMetaData(self, name=None):
        """Return a new metadata object connected to this engine.
        Queries executed against this metadata *will not* run in a
        separate thread.
        """

        return schema.BoundMetaData(self._engine, name)


    #
    # Connectable interface
    #
    # Note that SQLAlchemy will run the queries in autocommit mode.
    # Use transaction to run queries inside a transaction
    def contextual_connect(self):
        """Returns a Connection object which may be part of an ongoing
        context.
        """  

        # This can not return a deferred
        return self._engine.contextual_connect()
    
    def create(self, entity, **kwargs):
        """Creates a table or index given an appropriate schema
        object.
        """ 

        return self._deferToThread(self._engine.create, entity, **kwargs)
    
    def drop(self, entity, **kwargs):
        """Removes the entity from the database.
        """

        return self._deferToThread(self._engine.drop, entity, **kwargs)
    
    def execute(self, statement, *multiparams, **params):
        """Execute a query.
        """

        return self._deferToThread(self._engine.execute, statement,
                                   *multiparams, **params) 
 	    
    
    #
    # Engine interface
    #
    def transaction(self, callable_, *args, **kwargs):
        """Executes the given function within a transaction boundary.
        this is a shortcut for explicitly calling begin() and commit()
        and optionally rollback() when execptions are raised. 
        The given *args and **kwargs will be passed to the function,
        as well as the Connection used in the transaction.
        """
        
        return self._deferToThread(self._transaction, callable_,
                                   *args, **kwargs)

    def runCallable(self, callable_, *args, **kwargs):
        """Execute the given function.
        The given *args and **kwargs will be passed to the function,
        as well as the Connection used in the transaction.
        """
        
        return self._deferToThread(self._runCallable, callable_,
                                   *args, **kwargs)

    def executeCompiled(self, compiled, *multiparams, **params):
        return self._deferToThread(self._engine.execute_compiled,
                                   compiled, *multiparams, **params)

    #
    # Direct ResultProxy interface support
    #
    # The following methods are useful when the underlying cursor is
    # not thread safe (like pysqlite2)
    def fetchall(self, statement, *multiparams, **params):
        def helper(conn):
            return conn.execute(
                statement, *multiparams, **params
                ).fetchall()

        return self.runCallable(helper)

    def fetchone(self, statement, *multiparams, **params):
        def helper(conn):
            return conn.execute(
                statement, *multiparams, **params
                ).fetchone()

        return self.runCallable(helper)

    def scalar(self, statement, *multiparams, **params):
        def helper(conn):
            return conn.execute(
                statement, *multiparams, **params
                ).scalar()

        return self.runCallable(helper)

    def _transaction(self, callable_, *args, **kwargs):
        conn = self.contextual_connect()
        trans = conn.begin()
        try:
            ret = callable_(conn, *args, **kwargs)
            trans.commit()
            return ret
        except:
            trans.rollback()
            raise

    def _runCallable(self, callable_, *args, **kwargs):
        conn = self.contextual_connect()
        return callable_(conn, *args, **kwargs)
        
    def _deferToThread(self, f, *args, **kwargs):
        """Internal function.

        Call f in one of the connection pool's threads.
        """

        d = defer.Deferred()
        self.threadpool.callInThread(
            threads._putResultInDeferred,
            d, f, args, kwargs
            )

        return d

    #
    # Helper Decorators
    #
    def transact(self, f):
        def _wrap(*args, **kwargs):
            return self.transaction(f, *args, **kwargs)
            
        _wrap.__name__ = f.__name__
        return _wrap
        
    def transactSession(self, f):
        from sqlalchemy import orm

        def _wrap(*args, **kwargs):
            def _job(conn, *args, **kwargs):
                sess = orm.create_session(bind_to=self._engine)
                ret = f(conn, sess, *args, **kwargs)
                sess.flush()

                return ret
                
            return self.transaction(_job, *args, **kwargs)
        
        _wrap.__name__ = f.__name__
        return _wrap
        
#     def transact(self, allocSession=False):
#         """Decorator to be used to execute a function in a
#         transaction.
#         """

#         if allocSession:
#             return self._transact_session#(f)
#         else:
#             return self._transact#(f)
