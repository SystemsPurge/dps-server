import os
import json
from typing import Optional, Any,List,Dict
from delegate import delegate,client_delegate as cd, local_delegate as ld
from logging import Logger,basicConfig,_nameToLevel,getLogger
from pydantic import RootModel,BaseModel,Field,model_validator,ValidationError
from functools import reduce
class JTS(BaseModel):
    time: List[float|str] = Field(
        ..., 
        description="**Required.** A list of time values (e.g., timestamps or integer time steps)."
    )
    
    model_config = {
        "model_show_config":False,
        "extra": "allow",
        "json_schema_extra": {
            "example": {
                "time": [0.0, 0.5, 1.0, 1.5, 2.0],
                "sensor_x": [10.1, 10.2, 10.3, 10.4, 10.5],
                "sensor_y": [5.1, 5.2, 5.3, 5.4, 5.5],
                "temperature": [25.0, 25.1, 25.2, 25.1, 25.0]
            }
        }
    }
    
    @model_validator(mode='before')
    @classmethod
    def check_all_fields_are_list_of_float(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        #is json
        if not isinstance(data, dict):
            raise ValueError(f"Object must be a dict.")
        #is list
        for key, value in data.items():
            if not isinstance(value, list):
                raise ValueError(f"Field '{key}' must be a list.")
            if key == "time":
                continue
            #is float
            if not reduce(lambda x,y: x and (isinstance(y,float) or isinstance(y,int)),value,True):
                raise ValueError(f"Field '{key}' must be a list of float")
        return data

class TableRow(BaseModel):
    timestamp: float|str = Field(
        description="Timestamp of given measurement"
    )
    
    value: float = Field(
        description="Measured value"
    )
    
    profile_type: str = Field(
        description="What the measured value represents (e.g active power)"
    )
    
    model_config = {
        "extra": "allow",
        "model_show_config":False,
        "json_schema_extra": {
            "example": {
                "bus":"Some Bus Name"
            }
        }
    }

class JTSPost(BaseModel):
    pivot: bool = Field(
        ...,
        description=(
            "Set to true to pivot data given as a list of JSON elements."
            "Fields beside timestamp and value will be appended to the component's name."
        )
    )
    data: JTS|List[TableRow]
    model_config = {
        "model_show_config":False
    }
    
class JTSGet(RootModel[Dict[str,Dict[str,List[float]]]]):
    pass
class LstRes(BaseModel):
    lst:List[str]
    model_config = {
        "model_show_config":False
    }

class UpFileRes(BaseModel):
    filename: str
    model_config = {
        "model_show_config":False
    }

class params:
    name: str = os.urandom(6).hex()
    freq: int
    duration: int
    timestep: float
    opf: bool
    use_profile:Optional[str] = None
    replace_map:Optional[dict[str,str]] = None
    use_xml:str = None
    domain:str
    solver:str
    def __init__(self):
        pass
    
class _params(BaseModel):
    name: str = os.urandom(6).hex()
    freq: int
    duration: int
    timestep: float
    opf: bool
    use_profile:Optional[str] = None
    replace_map:Optional[dict[str,str]] = None
    use_xml:str = None
    domain:str
    solver:str
    model_config = {
        "model_show_config":False
    }

class interface:
    _d:delegate
    l:Logger
    _mode:str
    _defaults:dict[str,Any]
    def __init__(self,name:str):
        self._mode = interface._get_env('DPS_MODE')
        log_level = interface._get_env('DPS_LOG_LEVEL')
        p = interface._get_env('DPS_DEFAULTS')
        f = open(p,'r')
        content = f.read()
        self._defaults = json.loads(content)
        f.close()
        if log_level.upper() not in _nameToLevel:
            raise Exception(f'Unrecognized log level: {log_level}')
        basicConfig(level=_nameToLevel[log_level])
        self.l = getLogger(name.upper())
        self.l.info('Starting with: ')
        self.l.info(f'DPS_LOG_LEVEL={log_level}')
        self.l.info(f'DPS_MODE={self._mode}')
        self.l.info(f'DPS_DEFAULTS={p}')
        self.l.info(f'Defaults: {self._defaults}')
        if self._mode == 'client':
            sv_addr = interface._get_env('DPS_ADDR')
            self.l.info(f'DPS_ADDR={sv_addr}')
            self._d = cd(sv_addr)
        elif self._mode == 'local':
            root_dir = interface._get_env('DPS_ROOT')
            self.l.info(f'DPS_ROOT={root_dir}')
            self._d = ld(root_dir)
        else:
            raise Exception(f'Unrecognized mode: {self._mode}')
        
    
    def _get_env(env:str)->str:
        res = os.getenv(env)
        if res is None:
            raise Exception(f'Needed env variable {env} is not set')
        return res