from fastapi import FastAPI,UploadFile,HTTPException
from fastapi.responses import PlainTextResponse
from fdb import fdb
from models import interface,_params
import traceback
import json
from typing import Any


i = interface('API')
app = FastAPI()
    
#post ts of type <tstype>
@app.post("/ts/{tstype}")
async def post_ts(tstype:str,file:UploadFile):
    i.l.info(f'Got request to add file {file.filename}')
    if not fdb.isallowed(file.filename):
        raise HTTPException(status_code=400,detail=f'File type of {file.filename} is not allowed')
    try:
        i._d._tsaddraw(tstype,file.filename,file.file.read())
    except Exception as rre:
        raise HTTPException(status_code=400,detail=f'Error writing file: {rre}')
    return {'filename':file.filename}

#list ts of type <tstype>
@app.get("/ts/{tstype}")
async def list_ts(tstype:str):
    i.l.info(f'Got request to list resource {tstype}')
    try:
        return {tstype:i._d._tslist(tstype)}
    except Exception as rle:
        raise HTTPException(status_code=400,detail=f'Error listing {tstype}: {rle}')



#post ts as json
@app.post("/jts/{tstype}/{tsname}")
async def post_jts(tstype:str,tsname:str,body:dict[str,Any]):
    i.l.info(f'Got request to post resource {tstype} from body')
    try:
        content = json.dumps(body).encode('utf-8')
        tsname += '.json'
        i._d._tsaddraw(tstype,tsname,content)
    except Exception as rle:
        raise HTTPException(status_code=400,detail=f'Error adding json {tsname} of {tstype}: {rle}')
    
#get ts as json
@app.get("/jts/{tstype}/{tsname}")
async def get_jts(tstype:str,tsname:str):
    i.l.info(f'Got request to get resource {tsname} of {tstype} as json')
    try:
        return i._d._jtsget(tstype,tsname)
    except Exception as rle:
        raise HTTPException(status_code=400,detail=f'Error getting json {tsname} of {tstype}: {rle}')


#delete resource
@app.delete("/ts/{tstype}/{tsname}")
async def delete_ts(tstype:str,tsname:str):
    i.l.info(f'Got request to delete resource {tsname} of {tstype}')
    try:
        i._d._tsdelete(tstype,tsname)
    except Exception as rde:
        raise HTTPException(status_code=400,detail=f'Error deleting {tstype} {tsname}: {rde}')

#post xml
@app.post("/xml")
async def post_xml(file:UploadFile):
    i.l.info(f'Got request to add file {file.filename}')
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400,detail=f'Only archives are allowed at this ep')
    try:
        i._d._xaddraw(file)
    except Exception as rre:
        raise HTTPException(status_code=400,detail=f'Error writing file: {rre}')
    return {'filename':file.filename}

#list xml
@app.get("/xml")
async def list_xml():
    i.l.info(f'Got request to list resource xml')
    try:
        return {'xml':i._d._xlist()}
    except Exception as rle:
        raise HTTPException(status_code=400,detail=f'Error listing xml: {rle}')

#delete xml
@app.delete("/xml/{tsname}")
async def delete_xml(tsname:str):
    i.l.info(f'Got request to delete resource {tsname} of xml')
    try:
        i._d._xdelete(tsname)
    except Exception as rde:
        raise HTTPException(status_code=400,detail=f'Error deleting xml {tsname}: {rde}')

#post sim
@app.post("/s")
async def run_sim(p:_params):
    i.l.info(f'Got request to run simulation with parameters {p.model_dump()}')
    try:
        i._d._run(p.__dict__)
    except Exception:
        raise HTTPException(status_code=400,detail=f'Error running simulation: {traceback.format_exc()}')