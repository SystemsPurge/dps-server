from fastapi import FastAPI,UploadFile,HTTPException,File,Path
from fdb import fdb
from models import (
    interface,
    SimParameters,
    JsonTimeseriesResult,
    ListResult,
    TableRow,
    UploadFileResult
)
import traceback
import json
from typing import Any,List


def pivot_table(data: List[TableRow]):
    #to dicts
    dict_data = [d.model_dump() for d in data]
    #uniaue values and sort
    time:list[int] = list(set(map(lambda x: x["ts"],dict_data)))
    time.sort()

    base_keys = ["power_type","profile_type","value","ts"]
    result = {
        "active":{
            "timestamp":time
        },
        "reactive":{
            "timestamp":time
        }
    }
    for d in dict_data:
        try:
            #Extract profile_type value from data
            power_type:str = d.get("power_type")
            base_name:str = d.get("profile_type")
            ts_idx:int = time.index(d.get("ts"))
            #complement base name with all extra keys
            extra_keys:list[str] = [
                v for k,v in d.items() if k not in base_keys and isinstance(v,str)
            ]
            name = f'{base_name}_{'_'.join(extra_keys)}'
            #Check overlap of power_type and result keys (active, reactive)
            keyarr = [k for k in result.keys() if k in power_type.lower()]
            if len(keyarr) < 1:
                raise Exception(f'Cannot parse power_type into active or reactive')
            #len == 2 => power_type == reactive, since active in reactive and reactive in reactive
            key = 'reactive' if len(keyarr) == 2 else 'active'
            #if no key, prepare values
            if name not in result[key]:
                result[key][name] = [None]*len(time)
            
            result[key][name][ts_idx] = d.get("value")
        except Exception as e:
            raise Exception(f'Failed to pivot: {e}')
    return result

i = interface('API')
app = FastAPI()
    
#Upload a profile time series json.
@app.post("/jts/profile/{tsname}")
async def post_jts(
    body:List[TableRow],
    tsname:str=Path(
    description="The name of the time series being uploaded."    
    ))->UploadFileResult:
    """
    Upload a profile time series json.
    """
    i.l.info(f'Got request to post resource {"profile"} from body')
    try:
        data = pivot_table(body)
        tsname += '.json'
        i._d._tsaddraw("profile",tsname,json.dumps(data).encode('utf-8'))
    except Exception as rle:
        raise HTTPException(status_code=400,detail=f'Error adding json {tsname} of {"profile"}: {rle}')
    return {'filename':tsname}
    
#Get a result time series as json.
@app.get("/jts/result/{tsname}")
async def get_jts(
    tsname:str=Path(
    description="Name of time series to fetch"    
    )
    )->JsonTimeseriesResult:
    """
    Get a result time series as json.
    """
    i.l.info(f'Got request to get resource {tsname} of {"result"} as json')
    try:
        res = i._d._jtsget("result",tsname)
        res = res.get(tsname)
        res = {k:list(v.values()) for k,v in res.items()}
        res = {k:v for k,v in res.items() if not any([isinstance(_v,str) for _v in v])}
        return {'result':res}
    except Exception as rle:
        raise HTTPException(status_code=400,detail=f'Error getting json {tsname} of {"result"}: {rle}')

#Run a simulation.
@app.post("/s")
async def run_sim(p:SimParameters)->UploadFileResult:
    """
    Run a simulation.
    """
    i.l.info(f'Got request to run simulation with parameters {p.model_dump()}')
    try:
        i._d._run(p.model_dump())
    except Exception:
        raise HTTPException(status_code=400,detail=f'Error running simulation: {traceback.format_exc()}')
    return {'filename':p.name}

#Upload a profile time series file.
@app.post("/ts/profile",deprecated=True)
async def post_ts(
    file:UploadFile= File(
    description="An excel/csv spreadsheet"
))->UploadFileResult:
    """
    Upload a profile time series file.
    """
    i.l.info(f'Got request to add file {file.filename}')
    if not fdb.isallowed(file.filename):
        raise HTTPException(status_code=400,detail=f'File type of {file.filename} is not allowed')
    try:
        i._d._tsaddraw("profile",file.filename,file.file.read())
    except Exception as rre:
        raise HTTPException(status_code=400,detail=f'Error writing file: {rre}')
    return {'filename':file.filename}

#List time series data of a certain resource.
@app.get("/ts/{tstype}")
async def list_ts(tstype:str=Path(
    description="The type of the time series being fetched, one of profile or result"    
    ))->ListResult:
    """
    List time series data of a certain resource.
    """
    i.l.info(f'Got request to list resource {tstype}')
    try:
        return {'lst':i._d._tslist(tstype)}
    except Exception as rle:
        raise HTTPException(status_code=400,detail=f'Error listing {tstype}: {rle}')

#Delete a timseries from the file database.
@app.delete("/ts/{tstype}/{tsname}",deprecated=True)
async def delete_ts(
    tstype:str=Path(
    description="The type of the time series being deleted, one of profile or result"    
    ),
    tsname:str=Path(
    description="Name of the time series to delete"    
    )
)->UploadFileResult:
    """
    Delete a timseries from the file database.
    """
    i.l.info(f'Got request to delete resource {tsname} of {tstype}')
    try:
        i._d._tsdelete(tstype,tsname)
    except Exception as rde:
        raise HTTPException(status_code=400,detail=f'Error deleting {tstype} {tsname}: {rde}')
    return {'filename':tsname}

#Post CIM data archive.
@app.post("/xml")
async def post_xml(file:UploadFile=File(
    description="zip archive containing CIM xml profiles"
))->UploadFileResult:
    """
    Post CIM data archive.
    """
    i.l.info(f'Got request to add file {file.filename}')
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400,detail=f'Only archives are allowed at this ep')
    try:
        i._d._xaddraw(file)
    except Exception as rre:
        raise HTTPException(status_code=400,detail=f'Error writing file: {rre}')
    return {'filename':file.filename}

#List all CIM archive names.
@app.get("/xml")
async def list_xml()->ListResult:
    """
    List all CIM archive names.
    """
    i.l.info(f'Got request to list resource xml')
    try:
        return {'lst':i._d._xlist()}
    except Exception as rle:
        raise HTTPException(status_code=400,detail=f'Error listing xml: {rle}')


#Delete a system's CIM archive.
@app.delete("/xml/{xmlname}")
async def delete_xml(xmlname:str=Path(
    description="Name of the archive to delete"    
    ))->UploadFileResult:
    """
    Delete a system's CIM archive.
    """
    i.l.info(f'Got request to delete resource {xmlname} of xml')
    try:
        i._d._xdelete(xmlname)
    except Exception as rde:
        raise HTTPException(status_code=400,detail=f'Error deleting xml {xmlname}: {rde}')
    return {'filename':xmlname}