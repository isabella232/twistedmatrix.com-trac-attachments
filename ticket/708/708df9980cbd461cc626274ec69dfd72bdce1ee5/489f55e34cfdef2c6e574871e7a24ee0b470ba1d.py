import sys
from twisted.persisted.crefutil import _Dereference
from twisted.spread             import pb, jelly

class RemoteCopyable( pb.Copyable, pb.RemoteCopy ):  pass
jelly.globalSecurity.allowInstancesOf( RemoteCopyable )
pb.setCopierForClassTree( sys.modules[__name__], pb.Copyable )

if __name__ == '__main__':
    # circular object ref
    cell           = RemoteCopyable()
    cell.link      = RemoteCopyable()
    cell.link.cell = cell

    # Mimic sending across network
    broker         = pb.Broker()
    serializedCell = broker.serialize( cell )
    remoteCell     = broker.unserialize( serializedCell )

    print( _Dereference is type(remoteCell.link.cell) )
