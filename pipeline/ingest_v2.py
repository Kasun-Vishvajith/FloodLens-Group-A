"""Incremental real-data collection: 2016 onward. No fitted forecasting model.
Reuses the original verified ERA5/GloFAS archive when present. An empty checkout
can collect the same data from the APIs. Source transitions are retained per row.
"""
import argparse, datetime as dt, json, time, urllib.parse, gzip, hashlib
from pathlib import Path
import pandas as pd
from api_client import fetch, VARIABLES
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed-v2'

def main():
    p=argparse.ArgumentParser();p.add_argument('--as-of',default=dt.datetime.now(dt.timezone.utc).date().isoformat());p.add_argument('--start',default='2016-01-01');p.add_argument('--limit',type=int);a=p.parse_args()
    asof=pd.Timestamp(a.as_of);end=asof-pd.Timedelta(days=1);start=pd.Timestamp(a.start);era_end=asof-pd.Timedelta(days=7)
    if end<start or asof.date()>dt.datetime.now(dt.timezone.utc).date():p.error('Invalid or future collection date')
    OUT.mkdir(parents=True,exist_ok=True)
    locations=json.loads((ROOT/'pipeline/locations.json').read_text())[:a.limit]
    old_manifest={x['id']:x for x in json.loads((ROOT/'data/processed/manifest.json').read_text())} if (ROOT/'data/processed/manifest.json').exists() else {}
    prior={x['id']:x for x in json.loads((OUT/'manifest.json').read_text())} if (OUT/'manifest.json').exists() else {}
    manifest=[]
    for loc in locations:
        lid=loc['id'];print('Collecting '+loc['name'],flush=True)
        files=sorted((OUT/'hourly').glob(f'year=*/{lid}.csv.gz'))
        is_update=bool(files)
        h=pd.concat([pd.read_csv(f,parse_dates=['time']) for f in files],ignore_index=True) if files else pd.DataFrame(columns=['time']+VARIABLES)
        if not len(h) and lid in old_manifest:
            cached=ROOT/'data/raw'/(hashlib.sha256(old_manifest[lid]['weather_url'].encode()).hexdigest()+'.json.gz')
            if cached.exists():
                with gzip.open(cached,'rt') as f:h=pd.DataFrame(json.load(f)['response']['hourly'])
        h['time']=pd.to_datetime(h.time)
        h=h[(h.time>=start)&(h.time<end+pd.Timedelta(days=1))]
        if 'weather_model' not in h:h['weather_model']='ERA5'
        sources=prior.get(lid,{}).get('sources',[])
        if not sources and lid in old_manifest:sources=[{'product':'ERA5 original archive','url':old_manifest[lid]['weather_url'],'retrieved_at':old_manifest[lid]['weather_retrieved_at'],'grid':old_manifest[lid]['weather_grid']}]
        lo=max(start,h.time.max().normalize()+pd.Timedelta(days=1)) if len(h) else start
        if is_update and prior.get(lid,{}).get('as_of')!=a.as_of:lo=max(start,lo-pd.Timedelta(days=14))
        pieces=[h]
        grid=prior.get(lid,old_manifest.get(lid,{})).get('weather_grid')
        for left,right,model,label in [(lo,min(end,era_end),'era5','ERA5'),(max(lo,era_end+pd.Timedelta(days=1)),end,'ecmwf_ifs','ECMWF IFS recent')]:
            if left>right:continue
            # Annual chunks also allow a fully empty checkout to resume safely.
            for year in range(left.year,right.year+1):
                s=max(left,pd.Timestamp(year,1,1));e=min(right,pd.Timestamp(year,12,31))
                params=dict(latitude=loc['lat'],longitude=loc['lon'],start_date=str(s.date()),end_date=str(e.date()),hourly=','.join(VARIABLES),models=model,timezone='GMT',wind_speed_unit='kmh')
                url='https://archive-api.open-meteo.com/v1/archive?'+urllib.parse.urlencode(params)
                raw=fetch(url);r=raw['response'];expected_units={'precipitation':'mm','temperature_2m':'°C','relative_humidity_2m':'%','wind_speed_10m':'km/h','pressure_msl':'hPa'}
                if any(r.get('hourly_units',{}).get(k)!=u for k,u in expected_units.items()):raise ValueError('Unexpected weather units; refusing an incompatible join')
                piece=pd.DataFrame(r['hourly']);piece['time']=pd.to_datetime(piece.time);piece['weather_model']=label;pieces.append(piece)
                grid=[r['latitude'],r['longitude']]
                sources.append({'product':label,'url':url,'batch_source_url':raw.get('batch_source_url'),'retrieved_at':raw['retrieved_at'],'grid':grid})
                print(f'  weather {s.date()} to {e.date()}',flush=True)
        h=pd.concat(pieces,ignore_index=True).drop_duplicates('time',keep='last').sort_values('time')
        idx=pd.date_range(start,end+pd.Timedelta(hours=23),freq='h')
        h=h.set_index('time').reindex(idx).rename_axis('time').reset_index();h['location_id']=lid
        if h.time.duplicated().any():raise ValueError('Duplicate hourly key')
        for year,g in h.groupby(h.time.dt.year):
            dest=OUT/'hourly'/f'year={year}';dest.mkdir(parents=True,exist_ok=True);g.to_csv(dest/f'{lid}.csv.gz',index=False,compression={'method':'gzip','mtime':0})
        g=h.set_index('time').resample('D')
        daily=g.agg(rain=('precipitation',lambda s:s.sum(min_count=24)),temp=('temperature_2m','mean'),humidity=('relative_humidity_2m','mean'),wind=('wind_speed_10m','max'),pressure=('pressure_msl','mean'),tmax=('temperature_2m','max'),weather_model=('weather_model','first'))
        counts=g[VARIABLES].count()
        for dest,src in [('temp','temperature_2m'),('humidity','relative_humidity_2m'),('wind','wind_speed_10m'),('pressure','pressure_msl'),('tmax','temperature_2m')]:daily.loc[counts[src]<24,dest]=float('nan')
        daily.index.name='date';daily=daily.reset_index();daily['location_id']=lid
        q=pd.DataFrame(columns=['date','q','flow_source']);fg=None;collected_through=None
        if loc['river']:
            prev=OUT/f'daily-{lid}.csv.gz';old=ROOT/'dist/data'/f'{lid}.json'
            if prev.exists() or old.exists():
                q=pd.read_csv(prev,parse_dates=['date']) if prev.exists() else pd.DataFrame(json.loads(old.read_text())['rows'],columns=json.loads(old.read_text())['columns'])
                q['date']=pd.to_datetime(q.date)
                collected_through=q.date.max() if len(q) else None
                q=q[[c for c in ['date','q','flow_source'] if c in q]]
                if 'flow_source' not in q:q['flow_source']='GloFAS v4 consolidated'
                q=q[(q.date>=start)&(q.date<=end)&q.q.notna()]
            # Null flow is still a completed collection: revise the recent window,
            # rather than downloading ten years again at weather-only grid points.
            lo=max(start,collected_through+pd.Timedelta(days=1)) if collected_through is not None else start
            if prev.exists() and prior.get(lid,{}).get('as_of')!=a.as_of:lo=max(start,lo-pd.Timedelta(days=14))
            qs=[q];fg=prior.get(lid,old_manifest.get(lid,{})).get('flood_grid')
            if old_manifest.get(lid,{}).get('flood_url') and not any(x['product'].startswith('GloFAS') for x in sources):sources.append({'product':'GloFAS v4 consolidated original archive','url':old_manifest[lid]['flood_url'],'retrieved_at':old_manifest[lid]['flood_retrieved_at'],'grid':old_manifest[lid]['flood_grid']})
            for year in range(lo.year,end.year+1):
                s=max(lo,pd.Timestamp(year,1,1));e=min(end,pd.Timestamp(year,12,31))
                if s>e:continue
                url='https://flood-api.open-meteo.com/v1/flood?'+urllib.parse.urlencode(dict(latitude=loc['lat'],longitude=loc['lon'],start_date=str(s.date()),end_date=str(e.date()),daily='river_discharge'))
                raw=fetch(url);r=raw['response']
                if r.get('daily_units',{}).get('river_discharge')!='m³/s':raise ValueError('Unexpected discharge units')
                part=pd.DataFrame(r['daily']).rename(columns={'time':'date','river_discharge':'q'});part['date']=pd.to_datetime(part.date);part['flow_source']='GloFAS default seamless';qs.append(part);fg=[r['latitude'],r['longitude']]
                sources.append({'product':'GloFAS default seamless','url':url,'batch_source_url':raw.get('batch_source_url'),'retrieved_at':raw['retrieved_at'],'grid':fg})
                print(f'  discharge {s.date()} to {e.date()}',flush=True)
            q=pd.concat(qs,ignore_index=True).drop_duplicates('date',keep='last')
        daily=daily.merge(q,on='date',how='left',validate='one_to_one')
        for c in ['q']:daily[c]=pd.to_numeric(daily[c],errors='coerce')
        daily.to_csv(OUT/f'daily-{lid}.csv.gz',index=False,compression={'method':'gzip','mtime':0})
        entry={**loc,'weather_grid':grid,'flood_grid':fg,'hourly_rows':len(h),'missing_cells':int(h[VARIABLES].isna().sum().sum()),'flood_rows':int(daily.q.notna().sum()),'sources':list({x['url']:x for x in sources}.values()),'weather_model':'ERA5 with labelled recent IFS','flood_model':'GloFAS consolidated / seamless','era5_end':str(min(end,era_end).date()),'as_of':a.as_of}
        manifest.append(entry)
        # Preserve other locations during incremental runs, then normalize at completion.
        prior[lid]=entry;(OUT/'manifest.json').write_text(json.dumps(list(prior.values()),indent=2))
        print(f'  saved {len(h):,} hourly rows, {daily.q.notna().sum():,} flow days',flush=True)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));print('Collection complete.',flush=True)
if __name__=='__main__':main()
