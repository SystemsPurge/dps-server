import datetime
from delegate import client_delegate as cd
import json
from threading import Timer
from time import sleep
from typing import Any
from logging import getLogger,basicConfig,INFO
import cmath
basicConfig(level=INFO)
l =  getLogger('EXPORTER')
class exp:
    __c:cd = cd('http://localhost:5000')
    __rset:set[str] = set[str]()
    __promstr:str = ''
    def __init__(self):
        pass

    def __mag(self,jres:dict[str,Any])->dict[str,Any]:
        maxtime = len(list(jres['time'].keys()))
        newobj = {}
        for k in jres.keys():
            if k.endswith('_im'):
                im = jres[k]
                re = jres[k.replace('_im','_re')]
                mag:dict[str,Any] = dict[str,Any]()
                for i in range(maxtime):
                    idx = str(i)
                    mag[idx] = abs(cmath.sqrt(im[idx]**2+re[idx]**2))
                newobj[k.strip('_im')] = mag
            elif k.endswith('_re'):
                pass
            else:
                newobj[k] = jres[k]
            
        return newobj

    def __topromstr(self,jres:dict[str,Any],name:str)->Any:
        now = int(datetime.datetime.now().timestamp()*1000)
        newobj:dict[str,list[str]] = dict[str,Any]()
        for k in jres.keys():
            if k.find('_V') > -1:
                newkey = k.removesuffix('_V')
                num = self.__get_num(newkey)
                for n in num:
                    newkey = newkey.replace(n,'').strip('_')
                if any(c.isdigit() for c in newkey):
                    continue
                if newkey not in newobj:
                    newobj[newkey] = []
                for ts,v in jres[k].items():
                    newobj[newkey].append(f'{newkey}{{type="v",sim="{name}",num="{"_".join(num)}"}} {v} {now+int(ts)}')
            elif k.find('_I_') >-1:
                newkey = k.removesuffix(f'_I_{k[-1]}')
                num = self.__get_num(newkey)
                for n in num:
                    newkey = newkey.replace(n,'').strip('_')
                if any(c.isdigit() for c in newkey):
                    continue
                if newkey not in newobj:
                    newobj[newkey] = []
                for ts,v in jres[k].items():
                    newobj[newkey].append(f'{newkey}{{type="i",branch="branch{k[-1]}",sim="{name}",num="{"_".join(num)}"}} {v} {now+int(ts)}')
            elif k.find('_Q_') > -1 :
                newkey = k.removesuffix(f'_Q_{k[-1]}')
                num = self.__get_num(newkey)
                for n in num:
                    newkey = newkey.replace(n,'').strip('_')
                if any(c.isdigit() for c in newkey):
                    continue
                if newkey not in newobj:
                    newobj[newkey] = []
                for ts,v in jres[k].items():
                    newobj[newkey].append(f'{newkey}{{type="q",branch="branch{k[-1]}",sim="{name}",num="{"_".join(num)}"}} {v} {now+int(ts)}')
            elif k.find('_P_') > -1 :
                newkey = k.removesuffix(f'_P_{k[-1]}')
                num = self.__get_num(newkey)
                for n in num:
                    newkey = newkey.replace(n,'').strip('_')
                if any(c.isdigit() for c in newkey):
                    continue
                if newkey not in newobj:
                    newobj[newkey] = []
                for ts,v in jres[k].items():
                    newobj[newkey].append(f'{newkey}{{type="p",branch="branch{k[-1]}",sim="{name}",num="{"_".join(num)}"}} {v} {now+int(ts)}')
        return '\n'.join(
            list(
                map(lambda x: '\n'.join(x), list(newobj.values()))
            )
        )+'\n'

    def __rename_keys(self,jres:dict[str,Any])->dict[str,Any]:
        newobj = {}
        for k in jres.keys():
            n = k.strip().replace('.','_').replace(' ','_')
            newobj[n] = jres[k]
        return newobj
    def __get_num(self,k:str)->list[str]:
        parts = k.split('_')
        res = []
        for p in parts:
            if p.isnumeric():
                res.append(p)
            
        return res
    
    def get_promstr(self)->str:
        return self.__promstr
    
    def run(self):
        def periodic():
            newsets = set(self.__c._tslist('result')) - self.__rset
            for ns in newsets:
                l.info(f'Found new result {ns}')
                ns = ns.removesuffix('.csv')
                jres = list(self.__c._jtsget('result',ns).values())[0]
                jres = self.__rename_keys(jres)
                jres = self.__mag(jres)
                self.__promstr += self.__topromstr(jres,ns)
            self.__rset = self.__rset.union(newsets)
            sleep(10)
            periodic()
            

        Timer(5.0,periodic).start()
