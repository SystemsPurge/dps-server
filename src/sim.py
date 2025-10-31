from functools import reduce
from typing import Optional,Any,Callable
import dpsim
from logging import Logger,getLogger
import pandas as pd
from pandas import DataFrame
import pandapower as pp
from shutil import rmtree
from pandapower.converter import from_cim as cim2pp
import os 
import re
from fdb import fdb

class base_sim:        
    def __init__(
            self,
            name:str = os.urandom(6).hex(),
            freq:int = 50,
            duration:int=5,
            timestep:float=0.1,
            domain:str = 'SP',
            solver:str = 'NRP',
            opf:bool=False,
            use_profile:str = None,
            use_xml:str = None,
            replace_map:dict[str,str] = None
    ):
        
        self.name = name
        self.freq = freq
        self.duration = duration
        self.timestep = timestep
        self.opf = opf
        self.use_xml = use_xml
        self.use_profile = use_profile
        self.replace_map = replace_map
        if domain == "SP":
            self.domain = dpsim.Domain.SP
        elif domain == "DP":
            self.domain = dpsim.Domain.DP
        elif domain == "EMT":
            self.domain = dpsim.Domain.EMT
        else:
            raise Exception(f'Invalid sim domain: {domain}')

        if solver == "MNA":
            self.solver = dpsim.Solver.MNA
        elif solver == "NRP":
            self.solver = dpsim.Solver.NRP
        else:
            raise Exception(f'Invalid solver: {solver}')
    
    name: str
    freq: int
    duration: int
    timestep: float
    opf: bool
    use_profile:Optional[str]
    replace_map:Optional[dict[str,str]]
    use_xml:str
    domain: Any
    solver: Any
    
class state:
    configure:str = None
    preproc_profile:str = None
    opf:str = None
    sim:str = None
    
    def __init__(self):
        pass

class simulator(base_sim):
    
    _fdb:fdb
    @staticmethod
    def set_fdb(__fdb:fdb):
        simulator._fdb = __fdb
    mw_w=10e6
    system:Any
    xml:list[str]
    log:Logger
    __opf:Optional[DataFrame]
    __sim_names:list[str]
    __profile_names:set[str]
    __opf_names:set[str]
    __get_profile: Callable[[str,str],None]
    __loop:Callable
    __time:list[str]
    __costgens:list =[]
    state:state
    
    def __init__(
        self,
        name:str = os.urandom(6).hex(),
        freq:int = 50,
        duration:int=1440,
        timestep:float=0.1,
        domain:str = 'SP',
        solver:str = 'NRP',
        opf:bool=False,
        use_profile:str = None,
        use_xml:str = None,
        replace_map:dict[str,str] = None
    ):
        print(name,freq,duration,timestep,domain,solver,opf,use_profile,use_xml,replace_map)
        super().__init__(
            name,freq,duration,timestep,domain,solver,opf,use_profile,use_xml,replace_map
        )
        self.log = getLogger(f'SIM-{self.name}')

    def start(self):
        self.log.info('Starting simulation loop')
        self.__loop()
    
    def __stop(self):
        with open(f'logs/{self.name}.csv','br') as f:
            simulator._fdb.tsaddraw('result',self.name+'.csv',f.read())
        rmtree('logs')
        
    def configure(self) -> None:
        self.log.info('Configuring')
        self.replace_map  = {
            'lod': 'load',
            'sym': 'machine',
            'genstat': 'machine',
            'shntfix': 'fixed shunt',
            'shntswt': 'switched_shunt'
        }
        self.sim = dpsim.Simulation(self.name)
        self.__validate()
        self.sim.set_time_step(self.timestep)
        self.sim.set_final_time(self.duration)
        self.sim.set_domain(self.domain)
        self.sim.set_solver(self.solver)
        self.sim.set_solver_component_behaviour(dpsim.SolverBehaviour.Simulation)
        self.__add_log()
    
    def __add_log(self)->None:
        self.log.info('Adding logger')
        #set logger
        logger = dpsim.Logger(self.name)
        for node in self.system.nodes:
            logger.log_attribute(node.name()+'_V', 'v', node)
            
        for comp in self.system.components:
            if comp.__class__.__name__ =='PiLine':
                logger.log_attribute(comp.name() + '_I', 'current_vector', comp)
                logger.log_attribute(comp.name() + '_P', 'p_branch_vector', comp)
                logger.log_attribute(comp.name() + '_Q', 'q_branch_vector', comp)
            if comp.__class__.__name__ =='Transformer':
                logger.log_attribute(comp.name() + '_I', 'current_vector', comp)
                logger.log_attribute(comp.name() + '_P', 'p_branch_vector', comp)
                logger.log_attribute(comp.name() + '_Q', 'q_branch_vector', comp)

        self.sim.add_logger(logger)
    
    def __validate(self):
        self.log.info('Validating config')
        funcs:list[Callable[[str,str],None]] = list[Callable[[str,str],None]]()
        #get files
        if not self.use_profile and not self.use_xml:
            self.log.error('Require either profile or system for sim init')
            raise Exception('Require either profile or system for sim init')
        files = simulator._fdb.xmlget(self.use_xml)
        self.__set_sys(files)
        if self.use_profile:
            profiles = self.__preproc_profile()
            self.__profile_names = set(profiles.columns.values)
            
            def getp(comp:str,ts:str=None)->float:
                try:
                    if f'{comp}_p' in self.__profile_names:
                        self.sim.get_idobj_attr(comp,'P').set(profiles[profiles['DD/MM/YYYY HH:MM'] == ts][f'{comp}_p'].values[0]*simulator.mw_w)
                        self.log.debug(f'Found P value for {comp} at {ts}')
                    if f'{comp}_q' in self.__profile_names:
                        self.sim.get_idobj_attr(comp,'Q').set(profiles[profiles['DD/MM/YYYY HH:MM'] == ts][f'{comp}_q'].values[0]*simulator.mw_w)
                        self.log.debug(f'Found Q value for {comp} at {ts}')
                except:
                    pass
            funcs.append(getp)
            
        if self.opf:
            self.__run_opf(files)
            def repl0(comp:str,ts:str=None)->None:
                if comp in self.__opf_names:
                    try:
                        self.sim.get_idobj_attr(comp,'P').set(self.__opf[self.__opf['name'] == comp]['active power (MW)']*simulator.mw_w)
                        self.sim.get_idobj_attr(comp,'Q').set(self.__opf[self.__opf['name'] == comp]['reactive power (MVAR)']*simulator.mw_w)
                        self.log.debug(f'Found opf value for {comp}')
                    except Exception:
                        pass
            funcs.append(repl0)
        
        if len(funcs) == 0:
            def l():
                self.sim.run()
                self.log.info('Stopping simulation')
                self.__stop()
        else:
            def g(comp:str,ts:str=None):
                for func in funcs:
                    func(comp,ts)
            self.__get_profile = g
            if self.use_profile is not None:
                def l():
                    self.sim.start()
                    for ts in self.__time:
                        self.__assign_pq(ts)
                        self.sim.next()
                    self.log.info('Stopping simulation')
                    self.sim.stop()
                    self.__stop()
            else:
                def l():
                    self.sim.start()
                    t=0
                    while t<self.duration:
                        self.__assign_pq(str(t))
                        self.sim.next()
                        t+=self.timestep
                    self.log.info('Stopping simulation')
                    self.sim.stop()
                    self.__stop()
        self.__loop = l
    
    def __run_opf(self,files)->None:
        self.log.info('Running opf')
        net:pp.pandapowerNet = cim2pp.from_cim(file_list=files,use_GL_or_DL_profile='DL')
        indices = [pp.get_element_index(net,'gen',n) for n in list(net.gen['name'])]
        for i in indices:
            self.__costgens.append(pp.create_poly_cost(net,i,'gen',cp1_eur_per_mw=10))
        pp.runopp(net,delta=1e-16)
        base = pd.concat([net.shunt['name'], net.res_shunt], axis=1)
        for k in ['load','gen','sgen']:
            base = pd.concat([pd.concat([net[k]['name'], net[f'res_{k}']], axis=1),base])
            
        self.__opf = base[['p_mw','q_mvar','name']]
        self.__opf.rename({'p_mw':'active power (MW)','q_mvar':'reactive power (MVAR)'},inplace=True,axis=1)
        self.log.info(self.__opf)
        self.__opf_names = set(self.__opf['name'].values)
    
    def __assign_pq(self,timestamp:str)->None:
        for comp in self.__sim_names:
            self.__get_profile(comp,timestamp)

    def __set_sys(self,files:list[str])->None:
        self.log.info('Setting system')
        self.log.info(files)
        reader = dpsim.CIMReader(self.name)
        self.system = reader.loadCIM(self.freq, files, self.domain, dpsim.PhaseType.Single, dpsim.GeneratorType.PVNode)
        self.sim.set_system(self.system)
        self.__sim_names = [k for k, v in self.system.list_idobjects().items() if  v== 'SP::Ph1::Load' or  v== 'SP::Ph1::Shunt' or  v== 'SP::Ph1::SynchronGenerator']
        
    def __preproc_profile(self)->DataFrame:
        self.log.info('Preprocessing profiles')
        sheets = simulator._fdb.tsget('profile',self.use_profile)
        dfs = list(sheets.values())
        self.log.info(dfs)
        # Extract the datetime column from the first sheet (assuming the datetime column is the same across all sheets)
        time_col = dfs[0]['DD/MM/YYYY HH:MM']
        self.__time = time_col.dropna(how='all').values
        # Find common columns names (component name)
        def interset(pset:set[str],cdf:DataFrame):
            if len(cdf.columns.values) == 0:
                return pset
            return pset & set(cdf.columns.values)
        common_cols = reduce(interset,dfs,set(dfs[0].columns))
        common_cols.discard('DD/MM/YYYY HH:MM') # discard datetime column
        common_cols= [s for s in common_cols if 'Unnamed' not in s] # Remove column with 'Unnamed'

        profiles_dict= {
            'DD/MM/YYYY HH:MM':time_col
        }
        
        for col in common_cols:
            for sheet_name, df in sheets.items():
                if fdb.search_str(fdb.to_words(sheet_name),fdb.to_words('active power')) == 2:
                    profiles_dict[f'{col}_p'] = df[col]  # Add the active power profile data and extend column name with _p
                elif fdb.search_str(fdb.to_words(sheet_name),fdb.to_words('reactive power')) == 2:
                    profiles_dict[f'{col}_q'] = df[col]  # Add the reactive power profile data and extend column name with _q

        return self.__assign_comps(pd.DataFrame.from_dict(profiles_dict).dropna(how='all'))

    
    def __assign_comps(self,profiles:DataFrame)->DataFrame:
        self.log.info('Assigning components')
        def modify_string(s, replace_map):
            # Replace firt substring with the mapped substring
            for old, new in replace_map.items():
                s = s.replace(old, new)  # Replace each part of the string
            return s
        
        # List profiles component names
        profile_names  = list(profiles.columns.values)

        # List simulation component names
        sim_names= [k for k, v in self.system.list_idobjects().items() if  v== 'SP::Ph1::Load' or  v== 'SP::Ph1::Shunt' or  v== 'SP::Ph1::SynchronGenerator']

        # old:new
        rmap={}
        columns_to_extract=['DD/MM/YYYY HH:MM']
        # Iterate over simulation component names and check if they exist as a substring in profiles_comp_names
        for sim_name in sim_names:
            start_substring= modify_string(sim_name, self.replace_map)
            pattern = rf'^{re.escape(start_substring)}'
            matches = [s for s in profile_names if re.match(pattern, s)]
            if matches:
                for profile_name in matches:
                    t = re.search('(_p|_q)',profile_name)
                    if t:
                        suffix = t.group(1)
                        rmap[profile_name]= f'{sim_name}{suffix}'
                        columns_to_extract.append(profile_name)
                        self.log.debug(f"Profile component '{profile_name}' assigned to simulation component '{sim_name}{suffix}'")
            else:
                pass
                self.log.debug(f"No profile component found for simulation component '{sim_name}'")
                
        return profiles[columns_to_extract].rename(columns=rmap, inplace=False)
        