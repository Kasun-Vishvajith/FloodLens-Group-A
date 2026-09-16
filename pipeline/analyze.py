"""Build daily EDA, seasonal thresholds, extreme episodes and storage benchmarks. No model fitting."""
import datetime as dt, json, math, time
from pathlib import Path
import numpy as np
import pandas as pd
import sqlite3
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data/processed-v2';WEB=ROOT/'dist/data'
COLS=['date','rain','temp','humidity','wind','pressure','tmax','q','r3','r7','qp','rp','tp','wp','severity','weather_model','flow_source']

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    def clean(v):
        if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
        if isinstance(v,(list,tuple)):return [clean(x) for x in v]
        if isinstance(v,np.integer):return int(v)
        if isinstance(v,(float,np.floating)):return float(v) if math.isfinite(v) else None
        if v is pd.NA or v is pd.NaT:return None
        return v
    path.write_text(json.dumps(clean(obj),separators=(',',':'),allow_nan=False),encoding='utf-8')

def seasonal_percentile(series,months,baseline):
    result=pd.Series(np.nan,index=series.index); thresholds={}
    for month in range(1,13):
        reference=np.sort(series[baseline & (months==month)].dropna().values)
        thresholds[str(month)]={'p50':np.quantile(reference,.5) if len(reference) else None,'p95':np.quantile(reference,.95) if len(reference) else None,'p99':np.quantile(reference,.99) if len(reference) else None,'n':len(reference)}
        mask=(months==month)&series.notna()
        if len(reference):
            vals=series[mask].values
            # Midrank handles ties: all-zero reference days are not extremes.
            rank=(np.searchsorted(reference,vals,side='left')+np.searchsorted(reference,vals,side='right'))/(2*len(reference))*100
            result.loc[mask]=rank
    return result,thresholds

def main():
    started=time.perf_counter();manifest=json.loads((DATA/'manifest.json').read_text());WEB.mkdir(exist_ok=True,parents=True)
    frames={};events=[];location_summaries=[];lag_results={};baselines={}
    for loc in manifest:
        df=pd.read_csv(DATA/f"daily-{loc['id']}.csv.gz",parse_dates=["date"]).sort_values('date').reset_index(drop=True)
        if df.date.duplicated().any():raise ValueError('Duplicate daily key')
        if not df.date.diff().dropna().eq(pd.Timedelta(days=1)).all():raise ValueError('Nonconsecutive dates: reindex explicitly before rolling')
        df['rain']=df.rain.round(6)
        df['r3']=df.rain.rolling(3,min_periods=3).sum().round(6);df['r7']=df.rain.rolling(7,min_periods=7).sum().round(6)
        base=(df.date>='2016-01-01')&(df.date<'2021-01-01');months=df.date.dt.month;thresholds={}
        for variable,column in [('q','qp'),('r3','rp'),('tmax','tp'),('wind','wp')]:df[column],thresholds[variable]=seasonal_percentile(df[variable],months,base)
        maxp=df[['qp','rp','tp','wp']].max(axis=1)
        df['severity']=np.select([maxp>=99,maxp>=95,maxp.notna()],[2,1,0],default=-1)
        _,thresholds['rain']=seasonal_percentile(df.rain,months,base)
        df['district']=loc.get('district',loc['region']);frames[loc['id']]=df;baselines[loc['id']]=thresholds
        # Compare anomalies after removing seasonal monthly means; lag is association, not causation.
        rain_res=df.rain-df.groupby(months).rain.transform('mean');qres=df.q-df.groupby(months).q.transform('mean')
        lag_results[loc['id']]=[{'lag':lag,'r':rain_res.shift(lag).corr(qres),'n':int((rain_res.shift(lag).notna()&qres.notna()).sum())} for lag in range(8)] if loc['river'] else []
        event_mask=(df[['qp','rp']].max(axis=1)>=99)&(df.date>='2021-01-01')
        groups=event_mask.ne(event_mask.shift()).cumsum()
        for _,g in df[event_mask].groupby(groups[event_mask]):
            score=g[['qp','rp']].max(axis=1);peak=g.loc[score.idxmax()]
            # Within a saturated percentile tie, choose greatest relative discharge or rain.
            peak=g.loc[g.q.idxmax()] if g.q.notna().any() else g.loc[g.r3.idxmax()]
            events.append({'location_id':loc['id'],'start':g.date.min().strftime('%Y-%m-%d'),'end':g.date.max().strftime('%Y-%m-%d'),'peak_date':peak.date.strftime('%Y-%m-%d'),'duration':len(g),'peak_q':g.q.max(),'peak_r3':g.r3.max(),'score':float(score.max()),'kind':'High-flow / rainfall episode' if g.qp.max()>=99 else 'Extreme rainfall episode'})
        serial=df.copy();serial['date']=serial.date.dt.strftime('%Y-%m-%d')
        save(WEB/f"{loc['id']}.json",{'columns':COLS,'rows':serial[COLS].values.tolist()})
        loc.update(daily_rows=len(df),start=serial.date.min(),end=serial.date.max(),valid_q=int(df.q.notna().sum()),flood_nonzero=int((df.q>0).sum()),flood_unique=int(df.q.nunique()),max_q=df.q.max(),missing_daily=int(df[['rain','temp','humidity','wind','pressure','tmax']].isna().sum().sum()))
        location_summaries.append(loc)
    # Actual performance evidence on actual rows, never duplicated to inflate scale.
    ids={l['id'] for l in manifest};hourly_paths=sorted(p for p in (DATA/'hourly').glob('year=*/*.csv.gz') if p.name.removesuffix('.csv.gz') in ids);bench=[]
    db=DATA/'weather.sqlite';db.unlink(missing_ok=True)
    con=sqlite3.connect(db)
    for path in hourly_paths:
        pd.read_csv(path).to_sql('hourly_weather',con,if_exists='append',index=False,chunksize=1000)
    con.execute('CREATE INDEX idx_location_time ON hourly_weather(location_id,time)')
    total=con.execute('SELECT COUNT(*) FROM hourly_weather').fetchone()[0]
    for count in [total//4,total//2,total]:
        timings=[]
        for _ in range(3):
            t=time.perf_counter()
            con.execute("SELECT location_id, substr(time,1,7),sum(precipitation),avg(temperature_2m) FROM hourly_weather WHERE rowid<=? GROUP BY 1,2",(count,)).fetchall()
            timings.append(time.perf_counter()-t)
        bench.append({'rows':count,'files':len(hourly_paths),'seconds_median':float(np.median(timings)),'runs':timings})
    con.close()
    unique_grids=len(set(tuple(x['weather_grid']) for x in manifest));hrows=sum(x['hourly_rows'] for x in manifest)
    events.sort(key=lambda e:(e['duration'],e['peak_r3'] or 0),reverse=True)
    summary={'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'source_kind':'Real API data','hourly_rows':hrows,'daily_rows':sum(x['daily_rows'] for x in manifest),'flood_rows':sum(x.get('flood_rows',0) for x in manifest),'locations':location_summaries,'unique_weather_grids':unique_grids,'duplicate_weather_grids':len(manifest)-unique_grids,'weather_variables':5,'hourly_missing_cells':sum(x['missing_cells'] for x in manifest),'baseline_period':'2016–2020','start':min(x['start'] for x in manifest),'end':max(x['end'] for x in manifest),'historical_timezone':'UTC','events':events,'event_count':len(events),'benchmarks':bench,'compressed_csv_bytes':sum(p.stat().st_size for p in hourly_paths),'sqlite_bytes':db.stat().st_size,'raw_bytes':sum(p.stat().st_size for p in (ROOT/'data/raw').glob('*.gz')),'processing_seconds':time.perf_counter()-started,'source_urls':['https://open-meteo.com/en/docs/historical-weather-api','https://open-meteo.com/en/docs/flood-api','https://open-meteo.com/en/docs','https://open-meteo.com/en/docs/geocoding-api'],'as_of':manifest[0]['as_of'],'map_source':'https://www.geoboundaries.org/api/current/gbOpen/LKA/ADM2/','limitations':['River names describe geographic vicinity; channel identity has not been independently verified.','A monitored point does not represent an entire district or river basin.','ERA5 and GloFAS are modelled products, not local gauge measurements.','Percentile severity is an analytical heuristic, not an official warning or flood probability.','Recent IFS weather and forecast-backed GloFAS data differ from the older reanalysis products; source changes must be considered when interpreting trends.','No independently labelled flood-event ground truth was used; replay episodes are algorithmically identified.']}
    save(WEB/'summary.json',summary);save(WEB/'baselines.json',baselines);save(WEB/'lags.json',lag_results)
    combined=pd.concat(frames.values(),ignore_index=True)
    combined.to_csv(DATA/'daily-all.csv.gz',index=False,compression='gzip')
    combined.to_csv(WEB/'historical-daily.csv',index=False,na_rep='',float_format='%.5f')
    print(json.dumps({'hourly_rows':hrows,'unique_weather_grids':unique_grids,'events':len(events),'elapsed_seconds':summary['processing_seconds']},indent=2))

if __name__=='__main__':main()
