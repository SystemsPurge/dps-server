from fastapi import FastAPI,UploadFile,HTTPException,File,Path
from fastapi.responses import PlainTextResponse
from fdb import fdb
from models import interface,_params,JTSGet,LstRes,JTSPost,UpFileRes
import traceback
import json
from typing import Any


def pivot_table(data: list[dict[str,Any]]):
    time:list[int] = list(map(lambda x: x["timestamp"],data))
    time.sort()
    result = {
        "active":{
            "time":time
        },
        "reactive":{
            "time":time
        }
    }
    for d in data:
        pt = d.get("power_type")
        if d["profile_type"]+'_'+d["bus"] not in result[pt]:
            result[pt][d["profile_type"]+'_'+d["bus"]] = []
        result[pt][d["profile_type"]+'_'+d["bus"]].append(d["value"])
    return result

i = interface('API')
app = FastAPI()
    
#Upload a time series file of a certain resource.
@app.post("/ts/{tstype}")
async def post_ts(
    tstype:str= Path(
    description="The type of the time series being uploaded, one of profile or result"    
    ),
    file:UploadFile= File(
    description="An excel/csv spreadsheet"
))->UpFileRes:
    """
    Upload a time series file of a certain resource.
    """
    i.l.info(f'Got request to add file {file.filename}')
    if not fdb.isallowed(file.filename):
        raise HTTPException(status_code=400,detail=f'File type of {file.filename} is not allowed')
    try:
        i._d._tsaddraw(tstype,file.filename,file.file.read())
    except Exception as rre:
        raise HTTPException(status_code=400,detail=f'Error writing file: {rre}')
    return {'filename':file.filename}

#List time series files of a certain resource.
@app.get("/ts/{tstype}")
async def list_ts(tstype:str=Path(
    description="The type of the time series being fetched, one of profile or result"    
    ))->LstRes:
    """
    List time series files of a certain resource.
    """
    i.l.info(f'Got request to list resource {tstype}')
    try:
        return {'lst':i._d._tslist(tstype)}
    except Exception as rle:
        raise HTTPException(status_code=400,detail=f'Error listing {tstype}: {rle}')



#Upload a time series json.
@app.post("/jts/{tstype}/{tsname}")
async def post_jts(
    body:JTSPost,
    tstype:str=Path(
    description="The type of the time series being uploaded, one of profile or result"    
    ),
    tsname:str=Path(
    description="The name of the time series being uploaded."    
    ))->UpFileRes:
    """
    Upload a time series json.
    """
    i.l.info(f'Got request to post resource {tstype} from body')
    try:
        content = json.dumps(body).encode('utf-8')
        if "pivot" in content:
            data = pivot_table(content["data"])
        else:
            data = content["data"]
        tsname += '.json'
        i._d._tsaddraw(tstype,tsname,data)
    except Exception as rle:
        raise HTTPException(status_code=400,detail=f'Error adding json {tsname} of {tstype}: {rle}')
    return {'filename':tsname}
    
#Get a time series as json.
@app.get("/jts/{tstype}/{tsname}")
async def get_jts(
    tstype:str=Path(
    description="The type of the time series to fetch, one of profile or result"    
    ),
    tsname:str=Path(
    description="Name of time series to fetch"    
    )
    )->JTSGet:
    """
    Get a time series as json.
    """
    i.l.info(f'Got request to get resource {tsname} of {tstype} as json')
    try:
        return i._d._jtsget(tstype,tsname)
    except Exception as rle:
        raise HTTPException(status_code=400,detail=f'Error getting json {tsname} of {tstype}: {rle}')


#Delete a timseries from the file database.
@app.delete("/ts/{tstype}/{tsname}")
async def delete_ts(
    tstype:str=Path(
    description="The type of the time series being deleted, one of profile or result"    
    ),
    tsname:str=Path(
    description="Name of the time series to delete"    
    )
)->UpFileRes:
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
))->UpFileRes:
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
async def list_xml()->LstRes:
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
    ))->UpFileRes:
    """
    Delete a system's CIM archive.
    """
    i.l.info(f'Got request to delete resource {xmlname} of xml')
    try:
        i._d._xdelete(xmlname)
    except Exception as rde:
        raise HTTPException(status_code=400,detail=f'Error deleting xml {xmlname}: {rde}')
    return {'filename':xmlname}
    

#Run a simulation.
@app.post("/s")
async def run_sim(p:_params)->UpFileRes:
    """
    Run a simulation.
    """
    i.l.info(f'Got request to run simulation with parameters {p.model_dump()}')
    try:
        i._d._run(p.model_dump())
    except Exception:
        raise HTTPException(status_code=400,detail=f'Error running simulation: {traceback.format_exc()}')
    return {'filename':p.name}