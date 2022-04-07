import os,sys
from twisted.internet.defer import Deferred,inlineCallbacks,returnValue
from twisted.spread.util import StringPager,CallbackPageCollector,getAllPages, Pager
from twisted.spread import pb,flavors


        
class ListPager(Pager):
         """
         A simple pager that splits a List into chunks.
         @param collector: (twisted.spread.util.CallbackPageCollector)
         @param list_: a python list
         @param sendItems: (Integer) defaults to 100. This amount of list items will be transfered per page
         @keyword callback: a method which should be called after paging 
         """
         def __init__(self, collector, list_ ,sendItems=100, callback=None, *args, **kw):
             self.list = list_
             self.pointer = 0
             self.length=len(self.list)
             self.sendItems=sendItems
             Pager.__init__(self, collector, callback, *args, **kw)
     
         def nextPage(self):
             val = self.list[self.pointer:self.pointer+self.sendItems]
             self.pointer += self.sendItems
             if self.pointer >= self.length:
                 self.stopPaging()
             return val
         
         
         
class RemoteListPager(pb.Referenceable):
    '''This is a remote interface to ListPager
    @param list: a python list
    @param sendItems: (Integer) defaults to 100. This amount of list items will be transfered per page
    '''
    def __init__(self,list_,sendItems=100):
        self.list=list_
        self.sendItems=sendItems
        self.pager=None
        
    def destroy(self):
        '''This method should be called after paging. it tries to free memory'''
        del self.list
        del self.sendItems
        del self.pager
        del self
        
        
    def remote_startListPaging(self,pageCollector,*args,**kwargs):
        ''' Starts paging to given pageCollector
        @PARAM:
            pageCollector: (twisted.spread.util.callbackpager)
        @keyword:
         callback: a function which should be executed after paging. Defaults to self.destroy '''
            #maybe a callback could be added to delete the blob object when everything is done
        callback=kwargs.get('callback',None)  
        if callback==None:
            callback=self.destroy    
        self.pager=ListPager(pageCollector,self.list,self.sendItems,callback,*args,**kwargs)



class RemoteStringPager(pb.Referenceable):
    '''This is a remote Object to a string pager
    @param string: a Python string
    @param chunkSize: (Integer) Maximum string length
    '''
    def __init__(self,string,chunkSize=8192):
        self.string=string
        self.chunkSize=chunkSize
        self.pager=None
    
    def destroy(self):
        '''Method to free up the memory (hopefully)'''
        del self.string
        del self.pager
        del self
        
    def remote_startStringPaging(self,pageCollector,*args,**kwargs):
        ''' Starts paging to given pageCollector
        @PARAM:
            pageCollector: twisted.spread.util.callbackpager
        @keyword:
         callback: a function which should be executed after paging. Defaults to self.destroy '''
            #maybe a callback could be added to delete the blob object when everything is done
        callback=kwargs.get('callback',None)  
        if callback==None:
            callback=self.destroy    
        self.pager=StringPager(pageCollector,self.string,self.chunkSize,callback,*args,**kwargs)
        
        

class RemoteDictionaryItemPager(RemoteStringPager,RemoteListPager):
    '''This is a remote interface to a pager used for blobs contained in dictionaries'''
    def __init__(self,key,value,chunkSize=8192,sendItems=100):
        '''
        @param key: the key of the item which should be paged 
        @param value: the value related to key
        @param chunkSize: maximum chunk size for values which are basestrings
        @param sendItems: how much items to page if value is of type list 
        '''
        self.key=key
        self.item=value
        self.chunkSize=chunkSize 
        self.sendItems=sendItems
    
    def destroy(self):
        del self.key
        if hasattr(self,'list'):
            del self.list
        elif hasattr(self,'string'):
            del self.string
        if hasattr(self,'pager'):
            del self.pager
         
    def remote_startItemPaging(self,pageCollector,*args,**kwargs): 
        ''' Starts paging to given pageCollector
        @PARAM:
            pageCollector: twisted.spread.util.callbackpager
        @keyword:
         callback: a function which should be executed after paging. Defaults to self.destroy '''
        if isinstance(self.item,list):
            self.list=self.item
            del self.item
            self.remote_startListPaging(pageCollector,*args,**kwargs)
        elif isinstance(self.item,basestring):
            self.string=self.item
            del self.item
            self.remote_startStringPaging(pageCollector,*args,**kwargs)
            

    def remote_getKey(self):
        '''returns the return key of the object'''
        return self.key
    
    
    
class Transferable(object):
    '''Base class for transferable objects. These object are intend to be a container for data blobs'''
    
    def __init__(self):
        #this variable reflects the restored state
        self._restored=None
        #this variable reflects the remote state. It will be True on receiver side
        self.remote=False
        
    @property    
    def _restoreable(self):
        '''This property method checks if the Transferable is restoreable. That means, that the object has been
        transfered and not restored.
        '''
        if self.remote:
            if not self.restored:
                return True
            else:
                raise AttributeError,'object has already been restored!'
        else:
            raise AttributeError, 'object has not been send. Transfer it and then call %s.restore()' % self.__class__
        
    @property
    def _containsValidValue(self):
        '''This method checks if we can deliver the contained data element ''' 
        if self.remote:
            if not self.restored:
                raise AttributeError, 'object has not been restored!'
        return True
                     
    def restore(self):
        '''This method should restore an transfered Transferable on receiver side. It should return an Deferred to the restored Data Item.
        The class variable self.restored should be set to 'True' after successful restore.
        @return Deferred: (Deferred) should callback with restored data
        '''
        raise NotImpelementedError
    
    def getStateToCopy(self):
        '''This method should prepare the class dictionary so that it's safe to transfer.
        @return dict: the prepared class dictionary
        '''          
        raise NotImplementedError
    
    def _concat(self,pages):
        '''Simple method to concat strings / list
        @param pages: pages to concat
        @return: concatenated list / string
        '''
        c=None
        if not isinstance(pages,list):
            pages=list(pages)
        for page in pages:
            if c is None:
                c=page
            else:
                c+=page
        return c
    
    
    
class RemoteTransferable(flavors.RemoteCopy):
    ''' This is the base class for Transferables on receiver side'''
    def setCopyableState(self,state):
        '''This method is executed while reconstructing the object on receiver side.
        @param state: (dict) a python dictionary reflecting the state of the class
        '''
        self.__dict__=state
        self.restored=False
        self.remote=True



class TransferableString(flavors.Copyable,Transferable):
    '''A safe to transfer string container. Strings longer than chunkSize will be splited and paged
    @param string: a python string
    @param chunkSize: (Integer) max. string length to transfer in one piece'''
    def __init__(self,string,chunkSize=8192):
        if not isinstance(string,basestring):
            raise TypeError,'This is a container for strings!'
        self._string=string
        self.chunkSize=chunkSize
        Transferable.__init__(self)
        
    def __repr__(self):
        return self.string
    
    @property    
    def string(self):
        '''
        A Property which returns the contained string or raises an excpetion if the transfered string has
        not been restored
        '''
        if self._containsValidValue:
            return self._string
    
    def getStateToCopy(self):
        '''This method prepares the class dictionary so that it's safe to transfer.
        @return dict: the prepared class dictionary
        '''          
        d=self.__dict__.copy()
        if len(self._string)>=self.chunkSize:
                d['_string']=RemoteStringPager(d['_string'], self.chunkSize)
        return d
    
    def restore(self):
        '''This method restores the String on receiver side. It returns a Deferred and will callback with the 
        restored String
        @return: (Deferred)
        '''        
        def restored(pages,defer):
            #we will not get pages, if the string is empty, or not paged
            if not isinstance(pages,basestring):
                string=self._concat(pages)
            else:
                string=pages
            self.restored=True
            self._string=string
            defer.callback(string)
        if self._restoreable:
            defer=Deferred()
            if isinstance(self._string,pb.RemoteReference):
                df=getAllPages(self._string,'startStringPaging')
                df.addCallbacks(restored,defer.errback,[defer])
            else:
                restored(self._string,defer)
            return defer

class RemoteTransferableString(RemoteTransferable,TransferableString):
    '''
    This class represents a TransferableString on receiverside. For more info see TransferableString
    '''
    def __init__(self):
        RemoteTransferable.__init__(self)
        
flavors.setUnjellyableForClass(TransferableString, RemoteTransferableString) 



class TransferableDictionary(flavors.Copyable,Transferable):
    '''A safe to transfer Dictionary. Contained Lists and Strings will be prepared with the corresponding Transferable class
    @param dict_: (dict) the dictionary to transfer
    @param chunkSize: (Integer) maximum chunkSize for strings contained in the dict
    @param senditems: (Integer) maximum number of list items to transfer for lists contained in the dict  
    ''' 
    def __init__(self,dict_,chunkSize=8192,sendItems=100):
        if not isinstance(dict_,dict):
            raise TypeError,'This is a container for dict!'
        self._dict=dict_
        self.chunkSize=chunkSize
        self.sendItems=sendItems
        self._pagers=None
        Transferable.__init__(self)
        

    def getStateToCopy(self): 
        '''This method prepares the class dictionary so that it's safe to transfer.
        @return dict: the prepared class dictionary
        '''     
        newData={}
        pagers=[]
        d=self.__dict__.copy()
        for key,value in self._dict.items():
            pageIt=False
            if isinstance(value,basestring):
                if len(value)>=self.chunkSize:
                    pageIt=True
                    pagers.append(RemoteDictionaryItemPager(key,value,self.chunkSize,self.sendItems))
            elif isinstance(value,list):
                if len(value)>=self.sendItems:
                    pageIt=True
                    pagers.append(RemoteDictionaryItemPager(key,value,self.chunkSize,self.sendItems))
            elif isinstance(value,dict):
                    pageIt=True
            if pageIt:
                pagers.append(RemoteDictionaryItemPager(key,TranferableDictionary(value),self.chunkSize,self.sendItems))
            else:
                newData[key]=value 
            d['_dict']=newData
            d['_pagers']=pagers
        return d
    
     
    @inlineCallbacks
    def restore(self):
        '''restores the dictionary
        @RETURN: (Deferred) to restored dictionary'''
        if self._restoreable:
            if self._pagers is not None and self._pagers!=[]:
                if not isinstance(pagers,list):
                    pagers=list(pagers)
                    for pager in pagers:
                        key=yield pager.callRemote('getKey')
                        pages=yield getAllPages(pager, 'startItemPaging')
                        value=self._concat(pages)
                        self._dict[key]=value
            self.restored=True
            returnValue(self._dict)

    
    @property
    def dict(self):
        '''This method returns the contained dict if available - otherwise an execption is raised'''
        if self._containsValidValue:
            return self._dict
        
    def __repr__(self):
        return repr(self.dict)
        
   
        
class RemoteTransferableDictionary(RemoteTransferable,TransferableDictionary):
    '''
    This class represents a TransferableDictionary on receiver side. For more info see TransferableDictionary
    '''
    def __init__(self):
        RemoteTransferable.__init__(self)
        
flavors.setUnjellyableForClass(TransferableDictionary, RemoteTransferableDictionary)


class TransferableList(flavors.Copyable,Transferable):
    '''A safe to transfer List. Contained Dictionaries / Strings or Lists will be prepared with the corresponding Transferable class
    @param list_: (list) the list which should be prepared
    @param chunkSize: (Integer) maximum chunkSize for strings contained in the list
    @param senditems: (Integer) maximum number of list items to transfer for lists contained in the list  
    '''
    def __init__(self,list_,sendItems=100,chunkSize=8192):
        if not isinstance(list_,list):
            raise TypeError,'This is a container for list!'
        self._list=list_
        self.sendItems=sendItems
        self.chunkSize=chunkSize
        Transferable.__init__(self)
        
    @inlineCallbacks
    def restore(self):
        '''Collects the pieces of the list. Calls back the defer with the completed list
        @RETURN: (Deferred): to restored list'''
        if not self._restoreable:
            raise AttributeError,' list not restoreable'
        if isinstance(self._list,pb.RemoteReference):
            pages=yield getAllPages(self._list, 'startListPaging')
            list_=self._concat(pages)
            restored_list=[]
            for element in list(list_):
                #is this a Transferable?
                if isinstance(element,RemoteTransferableDictionary) or isinstance(element,RemoteTransferableList) \
                    or isinstance(element,RemoteTransferableString):
                    item=yield element.restore()
                #or just a trivial element?    
                else:
                    item=element
                restored_list.append(item)
            self._list=restored_list
        self.restored=True
        returnValue(self._list)
    
    @property
    def list(self):
        '''This method returns the contained list if available - an exception is raised otherwise'''
        if self._containsValidValue:
            return self._list
        
    def __repr__(self):
        return repr(self.list)
   
    def getStateToCopy(self):
        '''This method prepares the class dictionary so that it's safe to transfer.
        @return dict: the prepared class dictionary
        '''     
        d=self.__dict__.copy()
        preparedList=[]
        if self._list!=preparedList:
            for element in self._list:
                if isinstance(element,dict):
                    preparedList.append(TransferableDictionary(element,self.chunkSize,self.sendItems))
                elif isinstance(element,basestring):
                    preparedList.append(TransferableString(element,self.chunkSize))
                else:
                    preparedList.append(element)
            preparedList=RemoteListPager(preparedList,self.sendItems)
        d['_list']=preparedList
        return d
    
    
class RemoteTransferableList(RemoteTransferable,TransferableList):
    '''This class represents a Transferable list on receiver side. See TransferableList for more info'''
    def __init__(self):
        RemoteTransferable.__init__(self)

flavors.setUnjellyableForClass(TransferableList, RemoteTransferableList)

