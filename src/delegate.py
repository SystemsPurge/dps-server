
from typing import Any
import requests as rq
from fdb import fdb
from sim import simulator as s
from abc import abstractmethod,ABCMeta

class delegate(metaclass=ABCMeta):
    
    @abstractmethod
    def _run(self,body:dict[str,Any]):
        pass
    
    @abstractmethod
    def _tsadd(self,rtype:str,path:str):
        pass
    
    @abstractmethod
    def _jtsget(self,rtype:str,rname:str)->dict[str,Any]:
        pass
    
    @abstractmethod
    def _tsaddraw(self,rtype:str,rname:str,content:Any):
        pass
    
    @abstractmethod
    def _tsdelete(self,rtype:str,rname:str):
        pass
    
    @abstractmethod
    def _tslist(self,rtype:str)->list[str]:
        pass
    
    @abstractmethod
    def _xadd(self,path:str):
        pass
    
    @abstractmethod
    def _xdelete(self,rname:str):
        pass
    
    @abstractmethod
    def _xlist(self)->list[str]:
        pass
    
    @abstractmethod
    def _xaddraw(self,content:Any):
        pass

class client_delegate(delegate):
    __sv_addr:str
    def __init__(self,sv_addr:str):
        self.__sv_addr = sv_addr
    
    def _run(self,body:dict[str,Any])->None:
        try:
            res = rq.post(f'{self.__sv_addr}/s',json=body)
            res.raise_for_status()
        except rq.exceptions.RequestException as re:
            raise Exception(re.response.json()['detail'])
            
    def _tsadd(self,rtype:str,path:str)->None:
        try:
            files = {'file':open(path,'rb')}
            res = rq.post(f'{self.__sv_addr}/ts/{rtype}',files=files)
            res.raise_for_status()
        except rq.exceptions.RequestException as re:
            raise Exception(re.response.json()['detail'])
    
    def _tsaddraw(self,rtype:str,rname:str,content:Any)->None:
        try:
            files = {'file':content}
            res = rq.post(f'{self.__sv_addr}/ts/{rtype}',files=files)
            res.raise_for_status()
        except rq.exceptions.RequestException as re:
            raise Exception(re.response.json()['detail'])
            
    def _jtsget(self,rtype:str,rname:str)->dict[str,Any]:
        try:
            res = rq.get(f'{self.__sv_addr}/jts/{rtype}/{rname}')
            res.raise_for_status()
            return res.json()
        except rq.exceptions.RequestException as re:
            raise Exception(re.response.json()['detail'])
    
    def _tsdelete(self,rtype:str,rname:str)->None:
        try:
            res = rq.delete(f'{self.__sv_addr}/ts/{rtype}/{rname}')
            res.raise_for_status()
        except rq.exceptions.RequestException as re:
            raise Exception(re.response.json()['detail'])
            
        
    def _tslist(self,rtype:str)->list[str]:
        try:
            res = rq.get(f'{self.__sv_addr}/ts/{rtype}')
            res.raise_for_status()
            return res.json()[rtype]
        except rq.exceptions.RequestException as re:
            raise Exception(re.response.json()['detail'])
        
    def _xadd(self,path:str)->None:
        try:
            files = {'file':open(path,'rb')}
            res = rq.post(f'{self.__sv_addr}/xml',files=files)
            res.raise_for_status()
        except rq.exceptions.RequestException as re:
            raise Exception(re.response.json()['detail'])

    def _xaddraw(self,content:Any)->None:
        try:
            files = {'file':content}
            res = rq.post(f'{self.__sv_addr}/xml',files=files)
            res.raise_for_status()
        except rq.exceptions.RequestException as re:
            raise Exception(re.response.json()['detail'])
            
        
    def _xdelete(self,rname:str)->None:
        try:
            res = rq.delete(f'{self.__sv_addr}/xml/{rname}')
            res.raise_for_status()
        except rq.exceptions.RequestException as re:
            raise Exception(re.response.json()['detail'])
            
        
    def _xlist(self)->list[str]:
        try:
            res = rq.get(f'{self.__sv_addr}/xml')
            res.raise_for_status()
            return res.json()['xml']
        except rq.exceptions.RequestException as re:
            raise Exception(re.response.json()['detail'])
    
class local_delegate(delegate):
    __fdb:fdb
    def __init__(self,rootdir:str):
        self.__fdb = fdb(rootdir)

    def _run(self,body:dict[str,Any])->None:
        s.set_fdb(self.__fdb)
        print(body)
        sim = s(**body)
        sim.configure()
        sim.start()
    
    def _tsadd(self,rtype:str,path:str)->None:
        self.__fdb.tslink(rtype,path)
        
    def _tsaddraw(self,rtype:str,rname:str,content:Any):
        self.__fdb.tsaddraw(rtype,rname,content)
        
    def _jtsget(self,rtype:str,rname:str)->dict[str,Any]:
        return {x[0]:x[1].to_dict() for x in self.__fdb.tsget(rtype,rname).items()}
    
    def _tsdelete(self,rtype:str,rname:str)->None:
        self.__fdb.tsdelete(rtype,rname)
    
    def _tslist(self,rtype:str)->list[str]:
        return self.__fdb.tslist(rtype)
    
    def _xadd(self,path:str)->None:
        self.__fdb.xmllink(path)
    
    def _xaddraw(self, content:Any):
        self.__fdb.xmlput(content)
    
    def _xdelete(self,rname:str)->None:
        self.__fdb.xmldelete(rname)
    
    def _xlist(self)->list[str]:
        return self.__fdb.xmllist()