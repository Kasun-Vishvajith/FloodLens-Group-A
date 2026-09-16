"""Read-only analytics API. Serve with uvicorn backend.main:app --port 8001."""
from pathlib import Path
import json, os, time, urllib.request, urllib.parse, datetime as dt
from collections import deque
from threading import Lock
from functools import lru_cache
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'dist/data'
app=FastAPI(title='FloodLens Group A',version='3.0.0',description='Historical analytics and provider forecasts; no fitted prediction model.')
app.add_middleware(CORSMiddleware,allow_origins=os.getenv('FRONTEND_ORIGINS','http://localhost:8000,http://127.0.0.1:8000').split(','),allow_methods=['GET'],allow_headers=['*'])
def read(name):
    p=DATA/name
    if not p.exists():raise HTTPException(503,'Run the data pipeline first')
    return json.loads(p.read_text())
@app.get('/api/health')
def health():return {'status':'ok','storage':'PostgreSQL' if os.getenv('DATABASE_URL') else 'packaged JSON','forecast_source':'Open-Meteo'}
@app.get('/api/summary')
def summary():return read('summary.json')
@app.get('/api/locations')
def locations():return read('summary.json')['locations']
@app.get('/api/history/{location_id}')
def history(location_id:str,start:str=Query('2016-01-01',pattern=r'^\d{4}-\d{2}-\d{2}$'),end:str=Query('9999-12-31',pattern=r'^\d{4}-\d{2}-\d{2}$')):
    ids={l['id'] for l in locations()}
    if location_id not in ids:raise HTTPException(404,'Unknown monitoring location')
    try:dt.date.fromisoformat(start);dt.date.fromisoformat(end)
    except ValueError:raise HTTPException(422,'Invalid calendar date')
    if start>end:raise HTTPException(422,'Start must precede end')
    if os.getenv('DATABASE_URL'):
        import psycopg
        from psycopg.rows import dict_row
        with psycopg.connect(os.environ['DATABASE_URL'],row_factory=dict_row) as conn:
            records=conn.execute('SELECT * FROM daily_weather WHERE location_id=%s AND date BETWEEN %s AND %s ORDER BY date',(location_id,start,end)).fetchall()
        return {'location_id':location_id,'records':records,'storage':'PostgreSQL'}
    j=read(location_id+'.json')
    return {'location_id':location_id,'records':[dict(zip(j['columns'],r)) for r in j['rows'] if start<=r[0]<=end],'storage':'packaged JSON'}
@app.get('/api/analysis')
def analysis():return read('eda.json')
@app.get('/api/baselines')
def baselines():return read('baselines.json')
@app.get('/api/forecast-snapshot')
def snapshot():return read('current.json')
@app.get('/api/download')
def download():return FileResponse(DATA/'historical-daily.csv',filename='FloodLens-historical-daily.csv',media_type='text/csv')
# Fixed upstream hosts prevent arbitrary URL fetching. A five-minute cache reduces API calls.
upstream_requests=deque()
upstream_lock=Lock()
@lru_cache(maxsize=256)
def upstream(host,path,params,bucket):
    with upstream_lock:
        now=time.monotonic()
        while upstream_requests and now-upstream_requests[0]>=60:upstream_requests.popleft()
        if len(upstream_requests)>=180:raise HTTPException(429,'Provider request budget reached; retry in a minute')
        upstream_requests.append(now)
    url='https://'+host+path+'?'+params
    try:
        with urllib.request.urlopen(url,timeout=25) as response:j=json.load(response)
        if isinstance(j,dict) and j.get('error'):raise ValueError(j.get('reason'))
        return j
    except Exception as e:raise HTTPException(502,'Provider unavailable; retry later') from e
@app.get('/api/place')
def place(latitude:float=Query(...,ge=-90,le=90),longitude:float=Query(...,ge=-180,le=180)):
    p={'latitude':latitude,'longitude':longitude}
    bucket=int(time.time()//300)
    result={'requested':p,'retrieved_at':time.time(),'errors':{}}
    specs=[('weather','api.open-meteo.com','/v1/forecast',{**p,'current':'temperature_2m,relative_humidity_2m,wind_speed_10m,pressure_msl','daily':'precipitation_sum,temperature_2m_max,temperature_2m_min,wind_speed_10m_max','forecast_days':16,'timezone':'GMT'}),('flood','flood-api.open-meteo.com','/v1/flood',{**p,'daily':'river_discharge_median,river_discharge_p25,river_discharge_p75','models':'forecast_v4','forecast_days':16}),('elevation','api.open-meteo.com','/v1/elevation',p)]
    for key,host,path,params in specs:
        try:result[key]=upstream(host,path,urllib.parse.urlencode(params),bucket)
        except HTTPException:result[key]=None;result['errors'][key]='Provider unavailable'
    return result
@app.get('/api/search')
def search(name:str=Query(...,min_length=2,max_length=120)):
    return upstream('geocoding-api.open-meteo.com','/v1/search',urllib.parse.urlencode({'name':name,'count':12,'language':'en','format':'json'}),int(time.time()//300))

@app.get('/api/assets/{name}')
def asset(name:str):
    if name not in {'districts.geojson','lags.json'}:raise HTTPException(404,'Unknown asset')
    return read(name)
@app.get('/api/compact-history/{location_id}')
def compact_history(location_id:str):
    records=history(location_id,'2016-01-01','9999-12-31')['records']
    columns=['date','rain','temp','humidity','wind','pressure','tmax','q','r3','r7','qp','rp','tp','wp','severity','weather_model','flow_source']
    return {'columns':columns,'rows':[[str(r[c]) if c=='date' else r.get(c) for c in columns] for r in records]}
