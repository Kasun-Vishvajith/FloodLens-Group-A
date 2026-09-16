"""Refresh recent daily records and forecasts, validate a staged release, then publish.

Usage: python pipeline/update.py [--offline]
Offline rebuilds analytics using saved data without changing provider timestamps.
"""
import argparse
import csv
import datetime as dt
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
import pandas as pd
from config import ROOT, RAW_COLUMNS, VARIABLES
from provider import Client

ARCHIVE='https://archive-api.open-meteo.com/v1/archive'
FLOOD='https://flood-api.open-meteo.com/v1/flood'
WEATHER='https://api.open-meteo.com/v1/forecast'

def aggregate(response, label):
    expected={'precipitation':'mm','temperature_2m':'°C','relative_humidity_2m':'%','wind_speed_10m':'km/h','pressure_msl':'hPa'}
    if any(response.get('hourly_units',{}).get(k)!=v for k,v in expected.items()):raise ValueError('Unexpected weather units')
    frame=pd.DataFrame(response['hourly']);frame['time']=pd.to_datetime(frame.time)
    frame=frame.drop_duplicates('time',keep='last').set_index('time').sort_index()
    for k,low,high in [('precipitation',0,2000),('temperature_2m',-90,65),('relative_humidity_2m',0,100),('wind_speed_10m',0,500),('pressure_msl',800,1100)]:frame.loc[~frame[k].between(low,high),k]=float('nan')
    grouped=frame.resample('D')
    out=grouped.agg(rain=('precipitation',lambda x:x.sum(min_count=24)),temp=('temperature_2m','mean'),humidity=('relative_humidity_2m','mean'),wind=('wind_speed_10m','max'),pressure=('pressure_msl','mean'),tmax=('temperature_2m','max'))
    for target,source in [('rain','precipitation'),('temp','temperature_2m'),('humidity','relative_humidity_2m'),('wind','wind_speed_10m'),('pressure','pressure_msl'),('tmax','temperature_2m')]:out.loc[grouped[source].count()!=24,target]=float('nan')
    out.index.name='date';out=out.reset_index();out['date']=out.date.dt.strftime('%Y-%m-%d');out['weather_model']=label
    return out

def write_json(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')

def collect(stage, client, today):
    summary=json.loads((stage/'summary.json').read_text());end=today-dt.timedelta(days=1);era=today-dt.timedelta(days=7)
    for loc in summary['locations']:
        path=stage/(loc['id']+'.json');obj=json.loads(path.read_text());old=pd.DataFrame(obj['rows'],columns=obj['columns'])[RAW_COLUMNS]
        last=dt.date.fromisoformat(old.date.max())
        start=max(dt.date(2016,1,1),last-dt.timedelta(days=13))
        if last>end:raise ValueError('Archive is newer than requested clock; refusing to truncate it')
        weather=[];sources=loc.get('sources',[])
        for left,right,model,label in [(start,min(end,era),'era5','ERA5'),(max(start,era+dt.timedelta(days=1)),end,'ecmwf_ifs','ECMWF IFS recent')]:
            if left>right:continue
            # Bound every HTTP request to at most 31 days, including recovery after missed runs.
            while left<=right:
                stop=min(right,left+dt.timedelta(days=30))
                result=client.get(ARCHIVE,dict(latitude=loc['lat'],longitude=loc['lon'],start_date=str(left),end_date=str(stop),hourly=','.join(VARIABLES),models=model,timezone='GMT',wind_speed_unit='kmh'))
                response=result['response'];weather.append(aggregate(response,label));loc['weather_grid']=[response['latitude'],response['longitude']]
                sources.append(dict(product=label,url=result['url'],retrieved_at=result['retrieved_at'],grid=loc['weather_grid']))
                left=stop+dt.timedelta(days=1)
        fresh=pd.concat(weather,ignore_index=True)
        flows=[];left=start
        while left<=end:
            stop=min(end,left+dt.timedelta(days=30))
            result=client.get(FLOOD,dict(latitude=loc['lat'],longitude=loc['lon'],start_date=str(left),end_date=str(stop),daily='river_discharge'))
            response=result['response']
            if response.get('daily_units',{}).get('river_discharge')!='m³/s':raise ValueError('Unexpected discharge units')
            part=pd.DataFrame(response['daily']).rename(columns={'time':'date','river_discharge':'q'});part['flow_source']='GloFAS default seamless';flows.append(part)
            loc['flood_grid']=[response['latitude'],response['longitude']];sources.append(dict(product='GloFAS default seamless',url=result['url'],retrieved_at=result['retrieved_at'],grid=loc['flood_grid']))
            left=stop+dt.timedelta(days=1)
        fresh=fresh.merge(pd.concat(flows),on='date',how='left',validate='one_to_one')
        merged=pd.concat([old,fresh],ignore_index=True).drop_duplicates('date',keep='last').sort_values('date')
        expected=pd.date_range('2016-01-01',end,freq='D').strftime('%Y-%m-%d').tolist()
        merged=merged.set_index('date').reindex(expected).rename_axis('date').reset_index()
        merged=merged.astype(object).where(pd.notna(merged),None)
        write_json(path,dict(columns=RAW_COLUMNS,rows=merged[RAW_COLUMNS].values.tolist()))
        loc['sources']=list({x['url']:x for x in sources}.values());loc['as_of']=str(today)
        print('Updated',loc['name'],str(end),flush=True)
    summary['as_of']=str(today);write_json(stage/'summary.json',summary)

def forecasts(stage,client):
    ls=json.loads((stage/'summary.json').read_text())['locations']
    previous=json.loads((stage/'current.json').read_text())
    out={'origin':'Saved API snapshot','retrieved_at':dt.datetime.now(dt.timezone.utc).isoformat(),'weather':previous.get('weather',{}),'flood':previous.get('flood',{}),'weather_at':previous.get('weather_at',{}),'flood_at':previous.get('flood_at',{}),'errors':{}}
    for field in ['weather','flood']:
        for key in out[field]:out[field+'_at'].setdefault(key,previous.get('retrieved_at'))
    coords=dict(latitude=','.join(str(x['lat']) for x in ls),longitude=','.join(str(x['lon']) for x in ls))
    specs=[('weather',WEATHER,{**coords,'current':'temperature_2m,relative_humidity_2m,wind_speed_10m,pressure_msl','daily':'temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,precipitation_probability_max','timezone':'GMT','forecast_days':16}),('flood',FLOOD,{**coords,'daily':'river_discharge_median,river_discharge_p25,river_discharge_p75','forecast_days':16,'models':'forecast_v4'})]
    for field,url,params in specs:
        try:
            result=client.get(url,params);values=result['response']
            if not isinstance(values,list) or len(values)!=len(ls):raise ValueError('Provider location count mismatch')
            for loc,value in zip(ls,values):out[field][loc['id']]=value;out[field+'_at'][loc['id']]=result['retrieved_at']
        except Exception as error:
            out['errors'][field]=str(error);print('Keeping prior',field,'snapshot:',error,flush=True)
    write_json(stage/'current.json',out)
    return out

def export_forecast(stage):
    obj=json.loads((stage/'current.json').read_text())
    with (stage/'forecast-daily.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.writer(stream);writer.writerow(['location_id','date_utc','temperature_max_c','temperature_min_c','precipitation_mm','wind_max_kmh','rain_probability_max_pct','flow_median_m3s','flow_p25_m3s','flow_p75_m3s','weather_retrieved_utc','flood_retrieved_utc'])
        for lid,w in obj['weather'].items():
            d=w['daily'];fd=obj.get('flood',{}).get(lid,{}).get('daily',{});flow_dates=fd.get('time',[])
            for i,date in enumerate(d['time']):
                j=flow_dates.index(date) if date in flow_dates else None
                flow=[fd.get(k,[])[j] if j is not None else None for k in ['river_discharge_median','river_discharge_p25','river_discharge_p75']]
                writer.writerow([lid,date,*[d.get(k,[None]*len(d['time']))[i] for k in ['temperature_2m_max','temperature_2m_min','precipitation_sum','wind_speed_10m_max','precipitation_probability_max']],*flow,obj.get('weather_at',{}).get(lid,obj['retrieved_at']),obj.get('flood_at',{}).get(lid,obj['retrieved_at'])])

def promote(stage,destination):
    """Replace release directory with rollback on failure; builds consume only after success."""
    backup=destination.with_name('data.previous')
    if backup.exists():shutil.rmtree(backup)
    destination.rename(backup)
    try:stage.rename(destination)
    except BaseException:
        backup.rename(destination);raise
    shutil.rmtree(backup)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--offline',action='store_true',help='Recalculate saved archive without network requests');args=parser.parse_args()
    storage=ROOT/'data';storage.mkdir(exist_ok=True);lock=storage/'refresh.lock'
    try:handle=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:raise SystemExit('Another refresh holds data/refresh.lock; check its PID before removing a stale lock')
    os.write(handle,str(os.getpid()).encode());os.close(handle)
    run_id=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6]
    report={'run_id':run_id,'started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'offline':args.offline,'stages':{},'status':'running'};started=time.perf_counter();client=Client(run_id)
    try:
        with tempfile.TemporaryDirectory(prefix='floodlens-',dir=storage) as temp:
            stage=Path(temp)/'data';shutil.copytree(ROOT/'public/data',stage)
            if not args.offline:
                t=time.perf_counter();collect(stage,client,dt.datetime.now(dt.timezone.utc).date());report['stages']['collect']=time.perf_counter()-t
                t=time.perf_counter();forecasts(stage,client);report['stages']['forecasts']=time.perf_counter()-t
            export_forecast(stage)
            env={**os.environ,'FLOODLENS_DATA':str(stage)}
            for script in ['analyze.py','eda.py','validate.py']:
                t=time.perf_counter();subprocess.run([sys.executable,str(ROOT/'pipeline'/script)],cwd=ROOT,env=env,check=True);report['stages'][script]=time.perf_counter()-t
            release=json.loads((stage/'summary.json').read_text());report.update(archive_end=release['end'],release_id=release['release_id'])
            promote(stage,ROOT/'public/data')
            if not args.offline:
                snapshots=storage/'snapshots';snapshots.mkdir(exist_ok=True)
                with gzip.open(snapshots/(run_id+'.json.gz'),'wt') as stream:stream.write((ROOT/'public/data/current.json').read_text())
        report['status']='passed'
    except BaseException as error:
        report.update(status='failed',error=str(error));raise
    finally:
        report.update(finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),seconds=time.perf_counter()-started,http_attempts=sum(not e['cache_hit'] for e in client.events),cache_hits=sum(e['cache_hit'] for e in client.events),estimated_quota_units=sum(e['estimated_units'] for e in client.events))
        reports=storage/'runs';reports.mkdir(exist_ok=True);write_json(reports/(run_id+'.json'),report);write_json(storage/'refresh-status.json',report);lock.unlink()
        print(json.dumps(report,indent=2))
if __name__=='__main__':main()
