#!/usr/bin/env python

import os
import sys
from os.path import join
sys.path.insert(0, join(os.environ['HOME'], 'Twisted-trunk'))

from twisted.internet import reactor, defer, protocol
from twisted.conch.ssh import keys, agent

def _ebCreate(f):
  print f
  reactor.stop()

def main(args=None):
  if args is None:
    args = sys.argv[1:]

  cc = protocol.ClientCreator(reactor, agent.SSHAgentClient)
  d = cc.connectUNIX(os.environ['SSH_AUTH_SOCK'])
  d.addCallback(_cbGotLocal)
  d.addErrback(_ebCreate)
  reactor.run()
  return 0

def _cbGotLocal(agent):
  priv = keys.Key.fromFile(filename=join(os.environ['HOME'], '.ssh', 'id_rsa'),
                           passphrase='asdfg')
  d = agent.addIdentity(priv.privateBlob())
  d.addBoth(_cbAddIdentity, agent)

def _cbAddIdentity(ign, agent):
  priv = keys.Key.fromFile(filename=join(os.environ['HOME'], '.ssh', 'id_dsa'),
                           passphrase='wowee')
  d = agent.addIdentity(priv.privateBlob())
  d.addBoth(_cbAddDSA)

def _cbAddDSA(ign):
  print ign
  reactor.stop()

sys.exit(main())
