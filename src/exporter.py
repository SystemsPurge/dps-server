import datetime
import requests as rq
from threading import Timer
from time import sleep
from models import interface
from typing import Any
import os
import cmath

class metobj:
    __promstr:str
    _from:str
    _to:str
    
    def __init__(self,promstr:str,_f:str,_t:str):
        self.__promstr = promstr
        self._from = _f
        self._to = _t
    
    def get_str(self):
        if len(self.__promstr) == 0:
            return self.__promstr
        print(f"GIVING STR FOR FIRST TIME: {len(self.__promstr)}")
        old = self.__promstr
        self.__promstr = ''
        return old
class exp(interface):
    __met_url:str = None
    __with_met:bool = False
    __rset:set[str]
    __metobjs:dict[str,metobj]
    def __init__(self):
        try:
            os.environ['DPS_ADDR'] = 'http://localhost:5000'
            os.environ['DPS_MODE'] = 'client'
            super().__init__('export')
            met_url = os.getenv('DPS_MET_URL')
            if met_url is not None:
                self.__met_url = met_url
                self.__with_met = True
            self.__rset = set[str]()
            self.__metobjs = {}
        except Exception as e:
            self.l.error(f'ERROR PREPARING TASK: {e}')
            pass
    
    def get(self,name:str)->str:
        if name not in self.__metobjs:
            self.l.info(f'result {name} was not found')
            return ''
        return self.__metobjs[name].get_str()
    
    def run(self)->None:
        def periodic():
            results = set(self._d._tslist('result'))
            newsets = results - self.__rset
            oldsets = self.__rset - results
            changed = len(newsets) + len(oldsets) != 0
            #if anything changes
            if(changed):
                for ns in newsets:
                    self.l.info(f'Found new result {ns}')
                    ns = ns.removesuffix('.csv')
                    jres = list(self._d._jtsget('result',ns).values())[0]
                    jres = self.__rename_keys(jres)
                    jres = self.__mag(jres)
                    self.__add_res(ns,self.__tometobj(jres,ns))
                    if self.__with_met:
                        self.__add_app(ns)
                
                for os in oldsets:
                    self.l.info(f'Found old result {os}')
                    os = os.removesuffix('.csv')
                    self.__remove_res(os)
                    if self.__with_met:
                        self.__remove_app(os)
            
                self.__rset = results    
            sleep(10)
            periodic()
        
        Timer(5.0,periodic).start()
        
    def __add_app(self,sim:str)->None:
        try:
            #create task
            rq.post(f'{self.__met_url}/task',json={'name':sim,'apps':[],'categories':[],'metrics_path':f'/metrics/{sim}'})
            
            #create category
            rq.post(f'{self.__met_url}/category',json=self.__get_cat(sim))
            
            #create app
            rq.post(f'{self.__met_url}/app',json=self.__get_app(sim))
            
            #add category to task
            rq.put(f'{self.__met_url}/task/{sim}/category/{sim}')
            
            #add app to task
            rq.put(f'{self.__met_url}/task/{sim}/app',json=self.__get_params(sim))
            
            #start task
            rq.post(f'{self.__met_url}/op/{sim}/start',json=self.__get_freeze(sim))
        except Exception as e:
            self.l.error(f'ENCOUNTERED ERROR ADDING TO TASK: {e}')
    
    def __remove_app(self,sim:str)->None:
        try:
            #stop task
            rq.post(f'{self.__met_url}/op/{sim}/stop')
            
            #delete task
            rq.delete(f'{self.__met_url}/task/{sim}')
            
            #delete app
            rq.delete(f'{self.__met_url}/app/{sim}')
            
            #delete category
            rq.delete(f'{self.__met_url}/category/{sim}')
        except Exception as e:
            self.l.error(f'ENCOUNTERED ERROR ADDING TO TASK: {e}')
    
    def __add_res(self,name:str,content:metobj)->None:
        self.__metobjs[name] = content
    
    def __remove_res(self,name:str)->None:
        del self.__metobjs[name]
    
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

    def __tometobj(self,jres:dict[str,Any],name:str)->metobj:
        now = int(datetime.datetime.now().timestamp()*1000)
        metstrs:list[str] = []
        key = ''
        for k in jres.keys():
            if k.find('_V') > -1:
                key = 'voltage'
                comp = k.removesuffix('_V')
            elif k.find('_I_') >-1:
                key = 'current'
                comp = k.removesuffix(f'_I_{k[-1]}')+f'_{k[-1]}'
            elif k.find('_Q_') > -1 :
                key = 'reactive_power'
                comp = k.removesuffix(f'_Q_{k[-1]}')+f'_{k[-1]}'
            elif k.find('_P_') > -1 :
                key = 'active_power'
                comp = k.removesuffix(f'_P_{k[-1]}')+f'_{k[-1]}'
            else:
                continue
            for ts,v in jres[k].items():
                metstrs.append(f'{key}{{sim="{name}",comp="{comp}"}} {v} {now+int(ts)}')
        res = sorted(metstrs,key=lambda x: x.split(' ')[-1])
        start = res[0].split(' ')[-1]
        end = res[-1].split(' ')[-1]
        promstr = '\n'.join(
            res
        )+'\n'
        return metobj(promstr,start,end)

    def __rename_keys(self,jres:dict[str,Any])->dict[str,Any]:
        newobj = {}
        for k in jres.keys():
            n = k.strip().replace('.','_').replace(' ','_')
            newobj[n] = jres[k]
        return newobj
    
    def __get_cat(self,sim:str)->dict[str,Any]:
        return {
            'name':sim,
            'metric_aliases':['current','voltage','active_power','reactive_power']
        }
    
    def __get_app(self,sim:str)->dict[str,Any]:
        return {
            'name':sim,
            'metric_template':{
                'voltage':{
                    'legend_key':'{{comp}}',
                    'unit':'V',
                    'query':{
                        'name':'voltage',
                        'labels':{
                            'sim':sim
                        },
                        "aggr":{
                            "type":"none"
                        }
                    }
                },
                'current':{
                    'legend_key':'{{comp}}',
                    'unit':'A',
                    'query':{
                        'name':'current',
                        'labels':{
                            'sim':sim
                        },
                        "aggr":{
                            "type":"none"
                        }
                    }
                },
                'active_power':{
                    'legend_key':'{{comp}}',
                    'unit':'MW',
                    'query':{
                        'name':'active_power',
                        'labels':{
                            'sim':sim
                        },
                        "aggr":{
                            "type":"none"
                        }

                    }
                },
                'reactive_power':{
                    'legend_key':'{{comp}}',
                    'unit':'MVAR',
                    'query':{
                        'name':'reactive_power',
                        'labels':{
                            'sim':sim
                        },
                        "aggr":{
                            "type":"none"
                        }
                    }
                },
            }
        }
        
    def __get_params(self,sim:str)->dict[str,Any]:
        return {
            'app':sim,
            'deploy':{
                'deploy':False,
                'perf':False,
                'strict':False
            },
            'exports_metrics':True,
            'address':f'dps-server:5000',
            'active_port':5000
        }
    
    def __get_freeze(self,k):
        v = self.__metobjs[k]
        self.l.info(f'Freezing {k} {v._from} to {v._to}')
        return {'freeze':{k:{'from':v._from,'to':v._to}}}
