#!/usr/bin/env python

# Copyright (c) 2001-2007 Twisted Matrix Laboratories.
# See LICENSE for details.

import sys, os

from twisted import copyright
from twisted.python import dist

def main(args):
    if os.path.exists('twisted'):
        sys.path.insert(0, '.')
    from twisted.topfiles import setup as topsetup
    projects = ['', 'conch', 'lore', 'mail', 'names',
                'runner', 'web', 'words', 'news']
    scripts = []
    for i in projects:
        scripts.extend(dist.getScripts(i))
    setup_args = dict(
        # metadata
        name="Twisted",
        version=copyright.version,
        description="An asynchronous networking framework written in Python",
        author="Twisted Matrix Laboratories",
        author_email="twisted-python@twistedmatrix.com",
        maintainer="Glyph Lefkowitz",
        maintainer_email="glyph@twistedmatrix.com",
        url="http://twistedmatrix.com/",
        license="MIT",
        long_description="""\
    An extensible framework for Python programming, with special focus
    on event-based network programming and multiprotocol integration.

    It is expected that one day the project will expanded to the point
    that the framework will seamlessly integrate with mail, web, DNS,
    netnews, IRC, RDBMSs, desktop environments, and your toaster.
    """,

        packages=dist.getPackages('twisted'),
        data_files=dist.getDataFiles('twisted'),
        ext_modules=topsetup.extensions,
        scripts=scripts,
    )
    dist.setup(**setup_args)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        sys.exit(1)

