import argparse
import sys
import time

from cryptography.hazmat.backends.openssl import backend
from cryptography.hazmat.bindings.openssl import binding

from twisted.python import randbytes
from twisted.conch.ssh.transport import _getRandomNumber
from twisted.conch.ssh import _kex


def ygp():
    y = _getRandomNumber(randbytes.secureRandom, 512)
    g, p = _kex.getDHGeneratorAndPrime(
        b"diffie-hellman-group14-sha1")
    return y, g, p


_binding = binding.Binding()
_lib = _binding.lib
bn_ctx = _lib.BN_CTX_new()
_lib.BN_CTX_start(bn_ctx)


def python(g, y, p):
    pow(g, y, p)


def openssl(g, y, p):
    _y = backend._int_to_bn(y)
    _g = backend._int_to_bn(g)
    _p = backend._int_to_bn(p)

    _r = _lib.BN_CTX_get(bn_ctx)

    _lib.BN_mod_exp(_r, _g, _y, _p, bn_ctx)


def test(func, iterations):
    for _ in range(iterations):
        y, g, p = ygp()
        start = time.time()
        func(g, y, p)
        yield time.time() - start


def main():
    a = argparse.ArgumentParser(
        description="Compare pow to OpenSSL's bignums")
    a.add_argument("implementation", choices=("python", "openssl"))
    a.add_argument("--iterations", "-i",
                   type=int,
                   default=10000,
                   help="how many iterations to run")
    a.add_argument('--output', '-o',
                   type=argparse.FileType('w'),
                   default=sys.stdout)
    args = a.parse_args()
    func = globals()[args.implementation]
    for t in test(func, args.iterations):
        args.output.write("{}\n".format(t))


main()
