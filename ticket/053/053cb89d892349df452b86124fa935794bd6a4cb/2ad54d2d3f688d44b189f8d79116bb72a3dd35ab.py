# Monkey patch `twisted.protocols.ftp.decodeHostPort` and
# inherit from `twisted.protocols.ftp.FtpClient`
from twisted.internet import defer
from twisted.protocols.ftp import (
    FTPFileListProtocol, decodeHostPort, FTPCommand, _unwrapFirstError, _PassiveConnectionFactory)
from twisted.protocols.ftp import FTPClient as _FTPClient


def _decodeHostPort(line):
    if line.startswith("Entering Extended Passive Mode (|||"):
        # https://github.com/basvodde/filezilla/blob/8f874dfe2fdfee4a95cf706bc860252a5793c32e/src/engine/ftpcontrolsocket.cpp#L3789
        line = line[line.find("|||") + 3:]
        host = None
        port = int("".join([s for s in line if s.isdigit()]))
        if port <= 0 or port > 65535:
            raise ValueError("Bad port in EPSV response")
    else:
        abcdef = re.sub("[^0-9, ]", "", line)
        parsed = [int(p.strip()) for p in abcdef.split(",")]
        for x in parsed:
            if x < 0 or x > 255:
                raise ValueError("Out of range", line, x)
        a, b, c, d, e, f = parsed
        host = "%s.%s.%s.%s" % (a, b, c, d)
        port = (int(e) << 8) + int(f)
        pass
    return host, port

decodeHostPort = _decodeHostPort


class FTPClient(_FTPClient):
    def __init__(self, username, password, passive="EPSV"):
        """
        :param username: FTP user
        :param password: FTP pass
        :param passive: 'EPSV' (default) or 'PASV'
        """
        super(FTPClient, self).__init__(username=username,
                                        password=password,
                                        passive=passive)

    def _openDataConnection(self, commands, protocol):
        cmds = [FTPCommand(command, public=1) for command in commands]
        cmdsDeferred = defer.DeferredList([cmd.deferred for cmd in cmds],
                                          fireOnOneErrback=True, consumeErrors=True)
        cmdsDeferred.addErrback(_unwrapFirstError)

        if self.passive:
            _mutable = [None]

            def doPassive(response):
                host, port = decodeHostPort(response[-1][4:])
                if not host:
                    host = self.transport.addr[0]

                f = _PassiveConnectionFactory(protocol)
                _mutable[0] = self.connectFactory(host, port, f)

            pasvCmd = FTPCommand(self.passive)
            self.queueCommand(pasvCmd)
            pasvCmd.deferred.addCallback(doPassive).addErrback(self.fail)

            results = [cmdsDeferred, pasvCmd.deferred, protocol.deferred]
            d = defer.DeferredList(results, fireOnOneErrback=True, consumeErrors=True)
            d.addErrback(_unwrapFirstError)

            def close(x, m=_mutable):
                m[0] and m[0].disconnect()
                return x

            d.addBoth(close)

        for cmd in cmds:
            self.queueCommand(cmd)
        return d
