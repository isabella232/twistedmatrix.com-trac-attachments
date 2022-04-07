'''
Created on 25.09.2009

@author: bjoern
'''

from twisted.python import failure, log
import sys, os, time, gc
from twisted.trial import unittest
from twisted.spread import pb, util, publish, jelly
from twisted.internet import protocol, main, reactor
from twisted.internet.error import ConnectionRefusedError
from twisted.internet.defer import Deferred, gatherResults, succeed,inlineCallbacks,returnValue
from twisted.internet.threads import deferToThread
from remoteObjects.BlobDataHandler import *
from twisted.python import failure

class EchoTransferables(pb.Root):
    def remote_echo(self,inst):
        def inst_restored(value,defer):
            if isinstance(value,list):
                defer.callback(TransferableList(value))
            elif isinstance(value,basestring):
                defer.callback(TransferableString(value))
            elif isinstance(value,dict):
                defer.callback(TransferableDictionary(value))     
        defer=Deferred()
        d=inst.restore()
        d.addCallback(inst_restored,defer)
        return defer
    
class BlobHandlerTest(unittest.TestCase):


    def setUp(self):
        def got_root(root):
            self.ref=root
        self.server = reactor.listenTCP(0, pb.PBServerFactory(EchoTransferables()))
        self.clientFactory = pb.PBClientFactory()
        reactor.connectTCP("localhost", self.server.getHost().port,self.clientFactory)
        self.bigString='Senseless string' * 100
        self.longList=[150 * ['item']]
        self.longListBigString=[150 * [self.bigString]]
        self.dictBigString={'s':self.bigString}
        self.dictNestedInList=[self.dictBigString,self.dictBigString]
        return self.clientFactory.getRootObject().addCallback(got_root)
    
    @inlineCallbacks
    def _sendRestoreAndCompare(self,transferable,org_value,msg):
            echoed=yield self.ref.callRemote("echo", transferable)
            restored_res=yield echoed.restore()
            self.assertEquals(restored_res,org_value,msg)
    
    @inlineCallbacks
    def _sendAndTryToGetUnrestored(self,transferable,attribute,msg):
        echoed=yield self.ref.callRemote("echo", transferable)
        d=deferToThread(getattr(echoed, attribute))
        returnValue(d)
    
    @inlineCallbacks
    def _sendAndTryToPrintUnrestored(self,transferable,attribute,msg):
        echoed=yield self.ref.callRemote("echo", transferable)
        d=self.assertRaises(AttributeError, deferToThread(repr(echoed)))
        returnValue(d)
        
        
    def test_wrongInitializedString(self):
        self.failUnlessRaises(TypeError,TransferableString,[] )
        

    def test_wrongInitializedList(self):
        self.failUnlessRaises(TypeError,TransferableList,'')
        
    
    def test_wrongInitializedDictionary(self):
        self.failUnlessRaises(TypeError,TransferableDictionary,[])
        
    def test_TransferableList(self):
        org_inst = TransferableList(self.longListBigString)
        d=self._sendRestoreAndCompare(org_inst, self.longListBigString, 'List transfer failed!')
        return d

    def test_TransferableDictionary(self):
        org_inst = TransferableDictionary(self.dictBigString)
        d =self._sendRestoreAndCompare(org_inst,self.dictBigString,'Dictionary transfer failed!')
        return d

    def test_TransferableString(self):
        org_inst=TransferableString(self.bigString)
        d = self._sendRestoreAndCompare(org_inst, self.bigString, 'String transfer failed!')
        return d
    
    def test_dictNestedInList(self):
        org_inst=TransferableList(self.dictNestedInList)
        d=self._sendRestoreAndCompare(org_inst, self.dictNestedInList,'Transfer of dict nested in list failed!')
        return d
    
    def test_listNestedInList(self):
        listList=self.longList+list(self.longList)
        org_inst=TransferableList(listList)
        d=self._sendRestoreAndCompare(org_inst, listList, 'Transfer of nested list failed!')
        return d
    
    def test_listNestedInDict(self):
        listInDict={'s':self.longList}
        org_inst=TransferableDictionary(listInDict)
        d=self._sendRestoreAndCompare(org_inst, listInDict, 'Transfer of dictionary with nested list failed!')
        return d
    
    def test_dictNestedInDict(self):
        dictInDict=dict(self.dictBigString)['x']=self.dictBigString
        org_inst=TransferableDictionary(dictInDict)
        d=self._sendRestoreAndCompare(org_inst, dictInDict,'Transfer of dict nested in dict failed!' )
        return d
    
    def test_callToUnrestoredDict(self):
        org_inst=TransferableDictionary(self.dictBigString)
        d=self._sendAndTryToGetUnrestored(org_inst, 'dict', 'assess of unrestored dict did NOT fail!')
        d=self.assertFailure(d,AttributeError)
        return d
    
    def test_callToUnrestoredString(self):
        org_inst=TransferableString(self.bigString)
        d=self._sendAndTryToGetUnrestored(org_inst, 'string', 'assess of unrestored string did NOT fail!')
        d=self.assertFailure(d,AttributeError)
        return d
    
    def test_callToUnrestoredList(self):
        org_inst=TransferableList(self.longList)
        d=self._sendAndTryToPrintUnrestored(org_inst, 'list', 'assess of unrestored list did NOT fail!')
        d=self.assertFailure(d,AttributeError)
        return d
    
    def test_printUnrestoredDict(self):
        org_inst=TransferableDictionary(self.dictBigString)
        d=self._sendAndTryToPrintUnrestored(org_inst, 'dict', 'printing the unrestored  dict did NOT fail!')
        return self.assertFailure(d,AttributeError)
    
    def test_printUnrestoredString(self):
        org_inst=TransferableString(self.bigString)
        d=self._sendAndTryToPrintUnrestored(org_inst, 'string', 'printing the unrestored  string did NOT fail!')
        return self.assertFailure(d,AttributeError)
    
    def test_printUnrestoredList(self):
        org_inst=TransferableList(self.longList)
        d=self._sendAndTryToPrintUnrestored(org_inst, 'list', 'printing the unrestored list did NOT fail!')
        return self.assertFailure(d,AttributeError)
    
    def test_emptyList(self):
        org_inst=TransferableList([])
        d=self._sendRestoreAndCompare(org_inst, [], 'Failed to initialize TransferableList with empty list')
        return d
    
    def test_emptyString(self):
        org_inst=TransferableString('')
        d=self._sendRestoreAndCompare(org_inst, '', 'Failed to initialize TransferableString with empty string')
        return d
    
    def test_emptyDictionary(self):
        org_inst=TransferableDictionary({})
        d=self._sendRestoreAndCompare(org_inst, {}, 'Failed to initialize TransferableDictionary with empty dict')
        return d
    
    def tearDown(self):
        self.ref.broker.transport.loseConnection()
        return self.server.stopListening()
       



    

    