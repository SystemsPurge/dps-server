import json
import re
import os
from typing import Any,Callable
from models import params,interface

class flag:
    __exec:Callable[[Any],None]
    __valid:Callable[[str],Any]
    requires_arg:bool
    def __init__(self,exec:Callable[[Any],None],require_arg:bool,valid:Callable[[str],Any] = None):
        self.__exec = exec
        self.__valid = valid
        self.requires_arg = require_arg

    def run(self,arg:str = None):
        if arg is None:
            self.__exec()
            return
        self.__exec(self.__valid(arg))
    
class cli(interface):
    _defaults:dict[str,Any]
    p:params
    __flag_map:dict[str,flag]
    def __init__(self):
        super().__init__('cli')
        self.p = params()
        def mklset(attr:str)->Callable[[Any],None]:
            return lambda x: self.p.__setattr__(attr,x)

        self.__flag_map = {
            '-n':flag(mklset('name'),True,cli.__valid_str),
            '-f':flag(mklset('freq'),True,cli.__valid_num),
            '-d':flag(mklset('duration'),True,cli.__valid_num),
            '-t':flag(mklset('timestep'),True,cli.__valid_num),
            '-opf':flag(mklset('opf'),True,cli.__valid_bool),
            '-up':flag(mklset('use_profile'),True,cli.__valid_str),
            '-ux':flag(mklset('use_xml'),True,cli.__valid_str),
            '-dom':flag(mklset('domain'),True,cli.__valid_str),
            '-s':flag(mklset('solver'),True,cli.__valid_str),
        }
        if self._mode == 'client':
            self.__flag_map['-ux'] = flag(mklset('use_xml'),True,cli.__valid_str)
            self.__flag_map['-up'] = flag(mklset('use_profile'),True,cli.__valid_str)
        p = interface._get_env('DPS_DEFAULTS')
        with open(p) as f:
            self.l.info(f'DPS_DEFAULTS={p}')
            self._defaults = json.load(f)
    
    def run(self,args:list[str]):
        copy = self._defaults
        i = 0
        while i<len(args):
            c = args[i]
            if c not in self.__flag_map:
                raise Exception(f'Unrecognized flag: {c}')
            flag = self.__flag_map[c]
            if flag.requires_arg:
                cli.__check(args,i+2)
                flag.run(args[i+1])
                i+=2
            else:       
                flag.run()
                i+=1
            if c in copy:
                del copy[c]
        #fill defaults
        for k,v in copy.items():
            self.__flag_map[k].run(v)
        
        self._d._run(self.p.__dict__)
    
    def tslist(self,args:list[str]):
        cli.__check(args,1)
        res = self._d._tslist(args[0])
        self.l.info(f'----- {args[0].upper()} -----')
        for item in res:
            self.l.info(item)
    
    def tsdelete(self,args:list[str]):
        cli.__check(args,2)
        self._d._tsdelete(args[0],args[1])
    
    def tsadd(self,args:list[str]):
        cli.__check(args,2)
        self._d._tsadd(args[0],args[1])
    
    def jtsget(self,args):
        cli.__check(args,2)
        res = self._d._jtsget(args[0],args[1])
        if len(args)>=4 and args[2] == '-o':
            p = args[3]
            cli.__valid_path(p)
            with open(p,'wb') as f:
                f.write(json.dumps(res,indent=1).encode('utf-8'))
        else:
            self.l.info(json.dumps(res,indent=1))
    
    def xadd(self,args:list[str]):
        cli.__check(args,1)
        self._d._xadd(args[0])
    
    def xlist(self,args:list[str]):
        res = self._d._xlist()
        self.l.info(f'----- XML -----')
        for item in res:
            self.l.info(item)
    
    def xdelete(self,args:list[str]):
        cli.__check(args,1)
        self._d._xdelete(args[0])

    @staticmethod
    def __check(args:list[str],n:int):
        if len(args) < n:
            raise Exception('Missing arguments')
    
    @staticmethod
    def __valid_num(i:str)->float:
        if i.replace('.','').isnumeric():
            return float(i)
        raise Exception(f'{i} is not a number')

    @staticmethod
    def __valid_str(s:str)->str:
        return s
    
    @staticmethod
    def __valid_bool(b:str)->bool:
        if b == 'true' or b == 'false':
            return b == 'true'
        raise Exception(f'{b} is not a boolean')
    
    @staticmethod
    def __valid_path(p:str)->str:
        if p.startswith('.'):
            p.removeprefix('.')
        if not p.startswith('/'):    
            p = os.getcwd()+'/'+p
        exp = r'^(\/[\w-]+)+(.[a-zA-Z]+?)$'
        if re.match(exp,p) is not None:
            return p
        raise Exception(f'No such file or directory: {p}')