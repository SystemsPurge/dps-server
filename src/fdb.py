from pandas import DataFrame,read_excel,read_json,read_csv
import os 
from shutil import rmtree
from logging import Logger,getLogger
from fastapi import UploadFile
import re
import zipfile


class fdb:
    class __score:
        name:str
        score:int
        def __init__(self,name:str,score:int):
            self.name = name
            self.score = score

        def __eq__(self, other):
            return self.score == other.score

        def __lt__(self, other):
            return self.score < other.score
    class __tstype(str):
        pass
    class __subdir(str):
        pass
    
    __ts:dict[__tstype,__subdir] = {
        'profile':'profiles',
        'result':'results',
    }
    
    l:Logger
    __xmls:str = 'xmls'
    __archives:str= 'archives'
    __rootdir:str = 'rootdir'
    
    def __init__(self,rootdir:str):
        self.l=getLogger('FDB')
        self.__rootdir = rootdir
        self.l.info(f'Starting a files db at {rootdir}')
        os.makedirs(rootdir,exist_ok=True)
        for v in fdb.__ts.values():
            os.makedirs(self.__path(v),exist_ok=True)
        os.makedirs(self.__path('xmls'),exist_ok=True)
        os.makedirs(self.__path('archives'),exist_ok=True)
    
    def tsget(self,tstype:__tstype,tsname:str)->dict[str,DataFrame]:
        self.l.info(f'Getting timeseries {tsname} of {tstype}')
        self.__check(tstype)
        f = self.__search_files(tsname,fdb.__ts[tstype])[0]
        return fdb.__get(self.__path(fdb.__ts[tstype],f),f)
    
    def tsput(self,tstype:__tstype,tsname:str,*args:DataFrame)->None:
        self.l.info(f'Writing tiemseries {tsname} of {tstype}')
        self.__check(tstype)
        for df in args:
            df.to_json(self.__path(fdb.__resoruces[tstype],f'{tsname}-{df.name}'))
    
    def tsaddraw(self,tstype:__tstype,tsname:str,content:bytes):
        self.l.info(f'Adding raw {tsname} of {tstype}')
        self.__check(tstype)
        with open(self.__path(fdb.__ts[tstype],tsname),'bw') as f:
            f.write(content)
        df = self.tsget(tstype,tsname.split('.')[0]) #retrieve as df
        for c in df.columns:
            df.rename({c:c.strip()},inplace=True,axis=1)
        self.tsput(tstype,tsname,df)
        
        
    def tslist(self,tstype:__tstype)->list[str]:
        self.l.info(f'Listing resources of {tstype}')
        self.__check(tstype)
        return os.listdir(self.__path(fdb.__ts[tstype]))

    def tsdelete(self,tstype:__tstype,tsname:str)->None:
        self.l.info(f'Deleting resource {tstype} of {tsname}')
        self.__check(tstype)
        f = self.__search_files(tsname,fdb.__ts[tstype])[0]
        os.remove(self.__path(fdb.__ts[tstype],f))
    
    def tslink(self,tstype:__tstype,path:str)->None:
        self.l.info(f'Linking resource of {tstype} at {path}')
        self.__check(tstype)
        tsname = path.split('/')[-1]
        if not path.startswith('/'):
            path = os.getcwd()+'/'+path
        self.l.info(f'Linking file {tsname} in {path}')
        os.link(path,self.__path(fdb.__ts[tstype],tsname))
        
    def xmlget(self,xname:str)->list[str]:
        self.l.info(f'Getting xml file paths for{xname}')
        d = self.__path(fdb.__xmls,self.__search_files(xname,fdb.__xmls)[0])
        return [f'{d}/{f}' for f in os.listdir(d)]

    def xmlput(self,archive:UploadFile)->None:
        self.l.info(f'Writing archive {archive.filename}')
        fpath = self.__path(fdb.__archives,archive.filename)
        with open(fpath,'wb') as f:
            f.write(archive.file.read())
        if not zipfile.is_zipfile(fpath):
            os.remove(fpath)
            self.l.error(f'{archive.filename} is not an archive')
            raise Exception(f'{archive.filename} is not an archive')
        self.__unzip(archive.filename,fpath)
    
    def xmllist(self)->list[str]:
        self.l.info(f'Listing xml folders')
        res=os.listdir(self.__path(fdb.__xmls))
        return os.listdir(self.__path(fdb.__xmls))
    
    def xmldelete(self,xname:str):
        self.l.info(f'Deleting xml {xname}')
        d = self.__path(fdb.__xmls,self.__search_files(xname,fdb.__xmls)[0])
        rmtree(d)
    
    def xmllink(self,path:str)->None:
        self.l.info(f'Linking xml directory {path}')
        tsname = path.split('/')[-1]
        if not path.startswith('/'):
            path = os.getcwd()+'/'+path
        os.symlink(path,self.__path(fdb.__xmls,tsname))
    
    def __check(self,tstype:__tstype)->None:
        if not (tstype in fdb.__ts):
            self.l.error(f'No resource matches type {tstype}')
            raise Exception(f'No resource matches type {tstype}')
        
    @staticmethod
    def __get(path:str,fname:str)->dict[str,DataFrame]:
        if fdb.__ext(fname,'.json'):
            return {fname.strip('.json'):read_json(path)}
        elif fdb.__ext(fname,'.csv'):
            return {fname.strip('.csv'):read_csv(path)}
        else:
            return read_excel(path,sheet_name=None)
    
    def __unzip(self,archive:str,fpath:str)->None:
        xmlpath = self.__path(fdb.__xmls,archive.removesuffix('.zip')) 
        xmls = []
        self.l.info(f'Unzipping to {xmlpath}')
        os.mkdir(xmlpath)
        zr = zipfile.ZipFile(fpath,'r')
        for f in zr.namelist():
            if fdb.__ext(f,'.xml'):
                xmls.append(f)
            #maybe else->warn
        zr.extractall(xmlpath,members=xmls)
        if len(os.listdir(xmlpath)) == 0:
            os.rmdir(xmlpath)
        os.remove(self.__path(fdb.__archives,archive))
    
    def __path(self,*args:str)->str:
        return '/'.join([self.__rootdir,*args])
    
    def __search_files(self,rname:str,subdir:str,once:bool = True)->list[str]:
        fff = 'without' if once else 'with'
        self.l.info(f'Searching files for {rname} in {subdir} {fff} tolerance')
        words = fdb.to_words(rname)
        scores = [fdb.__score(f,fdb.search_str(fdb.to_words(f.split('.')[0]),words)) for f in os.listdir(self.__path(subdir))]
        scores = [s for s in scores if s.score > 0]
        scores.sort()
        if once:
            self.__exact_once(scores,rname,len(words))
        return [s.name for s in scores]
    
    @staticmethod
    def to_words(_str:str)->set[str]:
        _str = re.sub(r'[_-]',' ',_str).lower()
        res = {x for x in _str.split(' ')}
        return res
    
    @staticmethod
    def search_str(candidate:set[str],keywords:set[str])->int:
        return len(candidate.intersection(keywords))
    
    def __exact_once(self,files:list[__score],rname:str,lw:int)->None:
        if(len(files) == 0 or files[len(files)-1].score < lw):
            self.l.error(f'No resource found for {rname}')
            raise Exception(f'No resource found for {rname}')
        
        #if there is another element and its also an exact match
        elif len(files) > 1 and files[len(files)-2].score == lw:
            self.l.error(f'Conflict for {rname}: {", ".join([f.name for f in files])}')
            raise Exception(f'Conflict for {rname}: {", ".join([f.name for f in files])}')
    
    @staticmethod
    def __ext(tsname:str,ext:str)->bool:
        return tsname.endswith(ext)
    
    @staticmethod
    def isallowed(tsname:str)->bool:
        return fdb.__ext(tsname,'.json') or fdb.__ext(tsname,'.xls') or fdb.__ext(tsname,'.xlsx') or fdb.__ext(tsname,'.csv')