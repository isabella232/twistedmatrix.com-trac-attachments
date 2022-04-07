#!/bin/sh

VERSION=2.5.0
RPMBUILDDIR=`rpm --eval "%{_topdir}"`
SOURCE_TARBALL="Twisted-$VERSION.tar"
rm -f $RPMBUILDDIR/SOURCES/twisted-$VERSION || true
cp $SOURCE_TARBALL $RPMBUILDDIR/SOURCES
cp *.patch $RPMBUILDDIR/SOURCES
rpmbuild -ba --clean --rmsource twisted.spec
