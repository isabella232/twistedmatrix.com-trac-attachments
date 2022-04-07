from twisted.conch.ls import lsLine
from twisted.conch.ssh import filetransfer
from twisted.conch.ssh.filetransfer import FXF_READ, FXF_WRITE, FXF_APPEND, FXF_CREAT, FXF_TRUNC, FXF_EXCL
from zope.interface import implements
import sys
import os

class SFTPServerSession:

    implements(filetransfer.ISFTPServer)

    def __init__(self, avatar):
        self.avatar = avatar

    def _setAttrs(self, path, attrs):
        """
        NOTE: this function assumes it runs as the logged-in user:
        i.e. under _runAsUser()
        """
        if attrs.has_key("uid") and attrs.has_key("gid"):
            os.chown(path, attrs["uid"], attrs["gid"])
        if attrs.has_key("permissions"):
            os.chmod(path, attrs["permissions"])
        if attrs.has_key("atime") and attrs.has_key("mtime"):
            os.utime(path, (attrs["atime"], attrs["mtime"]))

    def _getAttrs(self, s):
        return {
            "size" : s.st_size,
            "uid" : s.st_uid,
            "gid" : s.st_gid,
            "permissions" : s.st_mode,
            "atime" : int(s.st_atime),
            "mtime" : int(s.st_mtime)
        }

    def _absPath(self, path):
        if sys.platform == 'win32' and len(path) > 0 and path[0] == '/':
            path = path[1:]
        path = os.path.abspath(path)
        return path

    def gotVersion(self, otherVersion, extData):
        return {}

    def openFile(self, filename, flags, attrs):
        return UnixSFTPFile(self, self._absPath(filename), flags, attrs)

    def removeFile(self, filename):
        filename = self._absPath(filename)
        return os.remove(filename)

    def renameFile(self, oldpath, newpath):
        oldpath = self._absPath(oldpath)
        newpath = self._absPath(newpath)
        res = os.rename(oldpath, newpath)
        return res
        

    def makeDirectory(self, path, attrs):
        path = self._absPath(path)
        os.makedirs(path)
        return self._setAttrs(path, attrs)

    def removeDirectory(self, path):
        path = self._absPath(path)
        os.rmdir(path)

    def realPath(self, path):
        path = self._absPath(path)

        if not sys.platform == 'win32':
            path = os.path.realpath(path)
        return path

    def extendedRequest(self, extName, extData):
        raise NotImplementedError

    def openDirectory(self, path):
        return UnixSFTPDirectory(self, self._absPath(path))

    def getAttrs(self, path, followLinks):
        path = self._absPath(path)
        if followLinks:
            s = os.stat(path)
        else:
            s = os.lstat(path)
        return self._getAttrs(s)


class UnixSFTPFile:

    implements(filetransfer.ISFTPFile)

    def __init__(self, server, filename, flags, attrs):
        self.server = server
        openFlags = 0
        if flags & FXF_READ == FXF_READ and flags & FXF_WRITE == 0:
            openFlags = os.O_RDONLY | os.O_BINARY
        if flags & FXF_WRITE == FXF_WRITE and flags & FXF_READ == 0:
            openFlags = os.O_WRONLY | os.O_BINARY
        if flags & FXF_WRITE == FXF_WRITE and flags & FXF_READ == FXF_READ:
            openFlags = os.O_RDWR | os.O_BINARY
        if flags & FXF_APPEND == FXF_APPEND:
            openFlags |= os.O_APPEND
        if flags & FXF_CREAT == FXF_CREAT:
            openFlags |= os.O_CREAT
        if flags & FXF_TRUNC == FXF_TRUNC:
            openFlags |= os.O_TRUNC
        if flags & FXF_EXCL == FXF_EXCL:
            openFlags |= os.O_EXCL
        if "permissions" in attrs:
            mode = attrs["permissions"]
            del attrs["permissions"]
        else:
            mode = 0777
        fd = os.open(filename, openFlags, mode)
        if attrs:
            server._setAttrs(filename, attrs)
        self.fd = fd

    def close(self):
        return os.close(self.fd)

    def readChunk(self, offset, length):
        os.lseek(self.fd, offset, 0)
        return os.read(self.fd, length)

    def writeChunk(self, offset, data):
        os.lseek(self.fd, offset, 0)
        return os.write(self.fd, data)

    def getAttrs(self):
        s = os.fstat(self.fd)
        return self.server._getAttrs(s)

    def setAttrs(self, attrs):
        raise NotImplementedError


class UnixSFTPDirectory:

    def __init__(self, server, directory):
        self.server = server
        self.files = os.listdir(directory)
        self.dir = directory

    def __iter__(self):
        return self

    def next(self):
        try:
            f = self.files.pop(0)
        except IndexError:
            raise StopIteration
        else:
            s = os.lstat(os.path.join(self.dir, f))
            longname = lsLine(f, s)
            attrs = self.server._getAttrs(s)
            return (f, longname, attrs)

    def close(self):
        self.files = []

