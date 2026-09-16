"""Recalculate full-archive retrospective analytics from published daily records."""
import datetime as dt
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import json
import math
import uuid
import numpy as np
import pandas as pd
from config import DATA, COLUMNS, START

def save(path,value):
    def clean(x):
        if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
        if isinstance(x,(list,tuple)):return [clean(v) for v in x]
        if isinstance(x,np.integer):return int(x)
        if isinstance(x,(float,np.floating)):return float(x) if math.isfinite(x) else None
        if x is pd.NA or x is pd.NaT:return None
        return x
    path.write_text(json.dumps(clean(value),ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')

def percentile(series,months):
    output=pd.Series(np.nan,index=series.index);thresholds={}
    for month in range(1,13):
        reference=np.sort(series[months.eq(month)].dropna().to_numpy())
        thresholds[str(month)]={f'p{n}':float(np.quantile(reference,n/100)) if len(reference) else None for n in [50,95,99]}
        thresholds[str(month)]['n']=len(reference)
        mask=months.eq(month)&series.notna()
        if len(reference)>=30:
            values=series[mask].to_numpy()
            output.loc[mask]=100*(np.searchsorted(reference,values,'left')+np.searchsorted(reference,values,'right'))/(2*len(reference))
    return output,thresholds

def derive(frame):
    frame=frame.copy().sort_values('date').reset_index(drop=True)
    frame['date']=pd.to_datetime(frame.date)
    if frame.date.duplicated().any() or not frame.date.diff().dropna().eq(pd.Timedelta(days=1)).all():raise ValueError('Daily keys must be unique and consecutive')
    frame['rain']=frame.rain.round(6)
    for n in [3,7]:frame[f'r{n}']=frame.rain.rolling(n,min_periods=n).sum().round(6)
    thresholds={};months=frame.date.dt.month
    for source,target in [('q','qp'),('r3','rp'),('tmax','tp'),('wind','wp')]:frame[target],thresholds[source]=percentile(frame[source],months)
    _,thresholds['rain']=percentile(frame.rain,months)
    peak=frame[['qp','rp','tp','wp']].max(axis=1)
    frame['severity']=np.select([peak>=99,peak>=95,peak.notna()],[2,1,0],default=-1)
    return frame,thresholds

def main():
    summary=json.loads((DATA/'summary.json').read_text());baselines={};lags={};events=[];combined=[]
    for loc in summary['locations']:
        obj=json.loads((DATA/(loc['id']+'.json')).read_text())
        frame,threshold=derive(pd.DataFrame(obj['rows'],columns=obj['columns']))
        baselines[loc['id']]=threshold
        residual_rain=frame.rain-frame.groupby(frame.date.dt.month).rain.transform('mean')
        residual_flow=frame.q-frame.groupby(frame.date.dt.month).q.transform('mean')
        lags[loc['id']]=[dict(lag=k,r=residual_rain.shift(k).corr(residual_flow),n=int((residual_rain.shift(k).notna()&residual_flow.notna()).sum())) for k in range(8)]
        mask=frame[['qp','rp']].max(axis=1)>=99
        groups=mask.ne(mask.shift()).cumsum()
        for _,group in frame[mask].groupby(groups[mask]):
            peak=group.loc[group.q.idxmax()] if group.q.notna().any() else group.loc[group.r3.idxmax()]
            events.append(dict(location_id=loc['id'],start=str(group.date.min().date()),end=str(group.date.max().date()),peak_date=str(peak.date.date()),duration=len(group),peak_q=group.q.max(),peak_r3=group.r3.max(),score=group[['qp','rp']].max().max(),kind='High-flow / rainfall episode' if group.qp.max()>=99 else 'Extreme rainfall episode'))
        frame['date']=frame.date.dt.strftime('%Y-%m-%d')
        save(DATA/(loc['id']+'.json'),dict(columns=COLUMNS,rows=frame[COLUMNS].values.tolist()))
        loc.update(start=frame.date.min(),end=frame.date.max(),daily_rows=len(frame),valid_q=int(frame.q.notna().sum()),flood_rows=int(frame.q.notna().sum()),flood_unique=int(frame.q.nunique()),flood_nonzero=int((frame.q>0).sum()),max_q=frame.q.max(),missing_daily=int(frame[['rain','temp','humidity','wind','pressure','tmax']].isna().sum().sum()))
        frame['location_id']=loc['id'];frame['district']=loc['district'];combined.append(frame)
    all_daily=pd.concat(combined,ignore_index=True)
    now=dt.datetime.now(dt.timezone.utc)
    summary.update(start=all_daily.date.min(),end=all_daily.date.max(),daily_rows=len(all_daily),flood_rows=int(all_daily.q.notna().sum()),generated_at=now.isoformat(),release_id=now.strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8],baseline_period=f"2016–{all_daily.date.max()[:4]}",baseline_start=START,baseline_end=all_daily.date.max(),baseline_method='Full-archive, same-calendar-month, retrospective midrank; past classifications may change after updates.',event_count=len(events),events=sorted(events,key=lambda x:(x['duration'],x['peak_r3'] or 0),reverse=True))
    # Do not inflate hourly evidence when updating only daily published data.
    summary['original_hourly_rows']=summary.get('original_hourly_rows',summary.get('hourly_rows'))
    summary['refresh_storage']='Daily published archive; original hourly collection is separate historical evidence.'
    save(DATA/'summary.json',summary);save(DATA/'baselines.json',baselines);save(DATA/'lags.json',lags)
    all_daily.to_csv(DATA/'historical-daily.csv',index=False,na_rep='',float_format='%.6f')
    print(f"Rebuilt {len(all_daily):,} daily rows; {len(events):,} episodes; baseline {summary['baseline_period']} through {summary['end']}")
if __name__=='__main__':main()
