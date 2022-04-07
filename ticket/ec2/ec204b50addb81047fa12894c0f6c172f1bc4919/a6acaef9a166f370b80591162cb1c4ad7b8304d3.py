import sys

import twisted.python.modules

def iterInterfaces(package):
    # First walk the direct attributes
    try:
        package.load()
    except Exception, e:
        sys.stderr.write('Cannot load %r: %r\n' % (package, e))
        return
    for attr in package.iterAttributes():
        name = attr.name.split('.')
        if not name[-1].startswith('_'):
            yield attr
    # Next walk the modules
    for module in package.iterModules():
        name = module.name.split('.')
        if name[-1] != 'test' and not name[-1].startswith('_'):
            for attr in iterInterfaces(module):
                yield attr


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: %s <path to Twisted checkout>" % (sys.argv[0],))

    # Clean up the Twisted we imported to get getModule
    saved = []
    for key, value in sys.modules.items():
        if key == 'twisted' or key.startswith('twisted.'):
            del sys.modules[key]
            if value is not None:
                saved.append(value)

    # Avoid importing twisted.internet.reactor, to avoid installing a reactor.
    sys.modules['twisted.internet.reactor'] = None

    sys.path.insert(0, sys.argv[1])

    targetTwisted = twisted.python.modules.getModule('twisted')
    sys.stderr.write('Found Twisted module at %r\n' % (targetTwisted.pathEntry,))
    for interface in iterInterfaces(targetTwisted):
        print interface.name


if __name__ == '__main__':
    main()
