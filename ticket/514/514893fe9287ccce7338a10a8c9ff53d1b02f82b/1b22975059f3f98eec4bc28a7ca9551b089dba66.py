# Running this test:
# trial tp_perf_test_v3.Test.test_std
#
# Trying the "qsize -> _qsize" mod:
# trial tp_perf_test_v3.Test.test_qsize_pool
#
# Profiling data gathered using cProfile.  twisted.trial.util uses
# standard "profile" by default; I modified it by hand on my install...

# NOTE: Assumes MySQL install, and access to DB via user "root".  If a
# password is required, please add it into db_args in the Test class.

from twisted.trial.unittest import TestCase
from twisted.enterprise.adbapi import ConnectionPool
from twisted.python.threadpool import ThreadPool
from twisted.internet import defer
import time


class QsizeModThreadPool(ThreadPool):

    def _startSomeWorkers(self):
        # MODIFICATION: qsize -> _qsize
        neededSize = self.q._qsize() + len(self.working)
        # Create enough, but not too many
        while self.workers < min(self.max, neededSize):
            self.startAWorker()


class QsizeModConnectionPool(ConnectionPool):

    def __init__(self, dbapiName, *connargs, **connkw):
        """Modified ConnectionPool using a modified ThreadPool."""

        from twisted.python import reflect  # MOD: Not already in namespace

        self.dbapiName = dbapiName
        self.dbapi = reflect.namedModule(dbapiName)

        if getattr(self.dbapi, 'apilevel', None) != '2.0':
            log.msg('DB API module not DB API 2.0 compliant.')

        if getattr(self.dbapi, 'threadsafety', 0) < 1:
            log.msg('DB API module not sufficiently thread-safe.')

        self.connargs = connargs
        self.connkw = connkw

        for arg in self.CP_ARGS:
            cp_arg = 'cp_%s' % arg
            if connkw.has_key(cp_arg):
                setattr(self, arg, connkw[cp_arg])
                del connkw[cp_arg]

        self.min = min(self.min, self.max)
        self.max = max(self.min, self.max)

        self.connections = {}  # all connections, hashed on thread id

        # these are optional so import them here
        import thread

        self.threadID = thread.get_ident
        self.threadpool = QsizeModThreadPool(self.min, self.max)  # MODIFIED

        from twisted.internet import reactor
        self.startID = reactor.callWhenRunning(self._start)


class Table(object):

    def __init__(self, pool, db_name, tbl_name="test"):
        self.pool = pool
        self.name = "%s.%s" % (db_name, tbl_name)
        self.iter = 0

    def create(self):
        create_query = (
            "CREATE TABLE IF NOT EXISTS %s "
            "(k INTEGER UNSIGNED NOT NULL,"   # key
            " ts TIMESTAMP NOT NULL,"         # timestamp (1 sec resolution)
            " i TINYINT UNSIGNED NOT NULL,"   # seq within timestamp
            " v INTEGER UNSIGNED NOT NULL,"   # value
            " PRIMARY KEY (k, ts, i),"
            " INDEX (ts)) "
            "ENGINE=innodb DEFAULT CHARSET=latin1;"
            ) % self.name
        return self.pool.runOperation(create_query)

    def insert(self, k, ts, v):
        query = "INSERT INTO %s VALUES (%%s, %%s, %%s, %%s)" % self.name
        ts_tuple = time.localtime(ts)
        ts_str = time.strftime("%Y-%m-%d %H:%M:%S", ts_tuple)
        i = self.iter
        self.iter = (self.iter + 1) % 64
        return self.pool.runOperation(query, (k, ts_str, i, v))


class Test(TestCase):

    timeout = 0x7FFFFFFF

    db_name = "perf_test"
    db_lib = "MySQLdb"
    db_args = {
        "user": "root",
        }

    def setUp(self):
        pool = ConnectionPool(self.db_lib, **self.db_args)

        def delete_if_exists(rows):
            dbs = [row[0] for row in rows]
            if self.db_name in dbs:
                return pool.runOperation(
                    "DROP DATABASE %s" % self.db_name)

        def create_db(_):
            return pool.runOperation("CREATE DATABASE %s" % self.db_name)

        existing_dbs = pool.runQuery("SHOW DATABASES")
        existing_dbs.addCallback(delete_if_exists)
        existing_dbs.addCallback(create_db)
        existing_dbs.addCallback(lambda x: pool.close())
        return existing_dbs

    @defer.inlineCallbacks
    def _do_test_core(self, pool_cls):
        pool = pool_cls(self.db_lib, **self.db_args)
        try:
            INNER_COUNT = 10000
            OUTER_COUNT = INNER_COUNT / 10
            tbl = Table(pool, self.db_name)
            yield tbl.create()
            ts_start_time = time.time()
            # Populate table
            for v in xrange(INNER_COUNT):  # Value iterator
                k = v % OUTER_COUNT  # Key iterator
                ts = int(time.time())
                yield tbl.insert(k, ts, v)
            ts_end_time = time.time()
            print "TIME TO RUN:", ts_end_time - ts_start_time
        finally:
            pool.close()

    def test_std(self):
        return self._do_test_core(ConnectionPool)

    def test_qsize_pool(self):
        return self._do_test_core(QsizeModConnectionPool)
