import os
from typing import Optional, Any
from delegate import delegate,client_delegate as cd, local_delegate as ld
from logging import Logger,basicConfig,_nameToLevel,getLogger
from pydantic import BaseModel
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
    dspf:bool
    pppf:bool
    use_profile:Optional[str] = None
    replace_map:Optional[dict[str,str]] = None
    use_xml:str = None
    domain:str
    solver:str

class interface:
    _d:delegate
    l:Logger
    _mode:str
    def __init__(self,name:str):
        self._mode = interface._get_env('DPS_MODE')
        log_level = interface._get_env('DPS_LOG_LEVEL')
        
        if log_level.upper() not in _nameToLevel:
            raise Exception(f'Unrecognized log level: {log_level}')
        
        basicConfig(level=_nameToLevel[log_level])
        self.l = getLogger(name.upper())
        self.l.info('Starting with: ')
        self.l.info(f'DPS_LOG_LEVEL={log_level}')
        self.l.info(f'DPS_MODE={self._mode}')
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