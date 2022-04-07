from twisted.logger import Logger
from twisted.cred import error, credentials
from twisted.internet import defer
from zope.interface import implementer
from twisted.cred.checkers import ICredentialsChecker

@implementer(ICredentialsChecker)
class CustomFilePasswordDB:
    """
    A file-based, text-based username/password database.

    Records in the datafile for this class are delimited by a particular
    string.  The username appears in a fixed field of the columns delimited
    by this string, as does the password.  Both fields are specifiable.  If
    the passwords are not stored plaintext, a hash function must be supplied
    to convert plaintext passwords to the form stored on disk and this
    CredentialsChecker will only be able to check L{IUsernamePassword}
    credentials.  If the passwords are stored plaintext,
    L{IUsernameHashedPassword} credentials will be checkable as well.
    """

    cache = False
    _credCache = None
    _cacheTimestamp = 0
    _log = Logger()

    def __init__(
        self,
        filename,
        delim=":",
        usernameField=0,
        passwordField=1,
        caseSensitive=True,
        hash=None,
        cache=False,
    ):
        """
        @type filename: L{str}
        @param filename: The name of the file from which to read username and
        password information.

        @type delim: L{bytes}
        @param delim: The field delimiter used in the file.

        @type usernameField: L{int}
        @param usernameField: The index of the username after splitting a
        line on the delimiter.

        @type passwordField: L{int}
        @param passwordField: The index of the password after splitting a
        line on the delimiter.

        @type caseSensitive: L{bool}
        @param caseSensitive: If true, consider the case of the username when
        performing a lookup.  Ignore it otherwise.

        @type hash: Three-argument callable or L{None}
        @param hash: A function used to transform the plaintext password
        received over the network to a format suitable for comparison
        against the version stored on disk.  The arguments to the callable
        are the username, the network-supplied password, and the in-file
        version of the password.  If the return value compares equal to the
        version stored on disk, the credentials are accepted.

        @type cache: L{bool}
        @param cache: If true, maintain an in-memory cache of the
        contents of the password file.  On lookups, the mtime of the
        file will be checked, and the file will only be re-parsed if
        the mtime is newer than when the cache was generated.
        """
        self.filename = filename
        self.delim = delim
        self.ufield = usernameField
        self.pfield = passwordField
        self.caseSensitive = caseSensitive
        self.hash = hash
        self.cache = cache

        if self.hash is None:
            # The passwords are stored plaintext.  We can support both
            # plaintext and hashed passwords received over the network.
            self.credentialInterfaces = (
                credentials.IUsernamePassword,
                credentials.IUsernameHashedPassword,
            )
        else:
            # The passwords are hashed on disk.  We can support only
            # plaintext passwords received over the network.
            self.credentialInterfaces = (credentials.IUsernamePassword,)

    def __getstate__(self):
        d = dict(vars(self))
        for k in "_credCache", "_cacheTimestamp":
            try:
                del d[k]
            except KeyError:
                pass
        return d

    def _cbPasswordMatch(self, matched, username):
        if matched:
            return username
        else:
            return failure.Failure(error.UnauthorizedLogin())

    def _loadCredentials(self):
        """
        Loads the credentials from the configured file.

        @return: An iterable of C{username, password} couples.
        @rtype: C{iterable}

        @raise UnauthorizedLogin: when failing to read the credentials from the
            file.
        """
        try:
            with open(self.filename, "r") as f:
                for line in f:
                    line = line.rstrip()
                    parts = line.split(self.delim)

                    if self.ufield >= len(parts) or self.pfield >= len(parts):
                        continue
                    if self.caseSensitive:
                        yield parts[self.ufield], parts[self.pfield]
                    else:
                        yield parts[self.ufield].lower(), parts[self.pfield]
        except OSError as e:
            self._log.error("Unable to load credentials db: {e!r}", e=e)
            raise error.UnauthorizedLogin()

    def getUser(self, username):
        """
        Look up the credentials for a username.

        @param username: The username to look up.
        @type username: L{bytes}

        @returns: Two-tuple of the canonicalicalized username (i.e. lowercase
        if the database is not case sensitive) and the associated password
        value, both L{bytes}.
        @rtype: L{tuple}

        @raises KeyError: When lookup of the username fails.
        """
        if not self.caseSensitive:
            username = username.lower()

        if self.cache:
            if (
                self._credCache is None
                or os.path.getmtime(self.filename) > self._cacheTimestamp
            ):
                self._cacheTimestamp = os.path.getmtime(self.filename)
                self._credCache = dict(self._loadCredentials())
            return username, self._credCache[username]
        else:
            for u, p in self._loadCredentials():
                if u == username:
                    return u, p
            raise KeyError(username)

    def requestAvatarId(self, c):
        try:
            u, p = self.getUser(c.username)
        except KeyError:
            return defer.fail(error.UnauthorizedLogin())
        else:
            up = credentials.IUsernamePassword(c, None)
            if self.hash:
                if up is not None:
                    h = self.hash(up.username, up.password, p)
                    if h == p:
                        return defer.succeed(u)
                return defer.fail(error.UnauthorizedLogin())
            else:
                return defer.maybeDeferred(c.checkPassword, p).addCallback(
                    self._cbPasswordMatch, u
                )


# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
An example FTP server with minimal user authentication.
"""

from twisted.protocols.ftp import FTPFactory, FTPRealm
from twisted.cred.portal import Portal
from twisted.cred.checkers import AllowAnonymousAccess, FilePasswordDB
from twisted.internet import reactor

#
# First, set up a portal (twisted.cred.portal.Portal). This will be used
# to authenticate user logins, including anonymous logins.
#
# Part of this will be to establish the "realm" of the server - the most
# important task in this case is to establish where anonymous users will
# have default access to. In a real world scenario this would typically
# point to something like '/pub' but for this example it is pointed at the
# current working directory.
#
# The other important part of the portal setup is to point it to a list of
# credential checkers. In this case, the first of these is used to grant
# access to anonymous users and is relatively simple; the second is a very
# primitive password checker.  This example uses a plain text password file
# that has one username:password pair per line. This checker *does* provide
# a hashing interface, and one would normally want to use it instead of
# plain text storage for anything remotely resembling a 'live' network. In
# this case, the file "pass.dat" is used, and stored in the same directory
# as the server. BAD.
#
# Create a pass.dat file which looks like this:
#
# =====================
#   jeff:bozo
#   grimmtooth:bozo2
# =====================
#
p = Portal(FTPRealm("./"), [AllowAnonymousAccess(), CustomFilePasswordDB("pass.dat")])

#
# Once the portal is set up, start up the FTPFactory and pass the portal to
# it on startup. FTPFactory will start up a twisted.protocols.ftp.FTP()
# handler for each incoming OPEN request. Business as usual in Twisted land.
#
f = FTPFactory(p)

#
# You know this part. Point the reactor to port 21 coupled with the above factory,
# and start the event loop.
#
reactor.listenTCP(21, f)
reactor.run()

