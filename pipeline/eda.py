"""Reproducible EDA and transparent screening scores; no model fitting."""
import datetime as dt,json,urllib.request,urllib.parse
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'dist/data'
KEYS=['rain','temp','humidity','wind','pressure','q']
def safe(v):return None if pd.isna(v) else float(v)

def risk_score(row, has_flow=True):
    """Return a transparent 0-100 latest-day screening score.

    The full score is weighted 50% flood severity, 30% recent cumulative
    rainfall, and 20% unusual weather. Percentiles are already normalized to
    0-100 by the analysis pipeline. When a component is unavailable, the
    remaining weights are rescaled and the basis is labelled explicitly.
    """
    weights={'flood':.50,'rainfall':.30,'weather':.20}
    values={
        'flood': safe(row.get('qp')) if has_flow else None,
        'rainfall': safe(row.get('rp')),
        'weather': max((v for v in (safe(row.get('tp')),safe(row.get('wp'))) if v is not None),default=None),
    }
    available={k:v for k,v in values.items() if v is not None}
    if not available:
        return {'score':None,'basis':'Unavailable','components':values,'weights':{}}
    total=sum(weights[k] for k in available)
    applied={k:weights[k]/total for k in available}
    score=sum(available[k]*applied[k] for k in available)
    names={'flood':'flood 50%','rainfall':'rainfall 30%','weather':'weather 20%'}
    basis=' + '.join(names[k] for k in ('flood','rainfall','weather') if k in available)
    if len(available)<3:basis+=' (available weights rescaled)'
    return {'score':float(score),'basis':basis,'components':values,'weights':applied}
def main():
    summary=json.loads((DATA/'summary.json').read_text());ls=summary['locations'];out={'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'locations':{},'ranking':[]}
    ep=DATA/'elevation.json';elevation=json.loads(ep.read_text()) if ep.exists() else {}
    missing=[l for l in ls if l['id'] not in elevation]
    if missing:
        try:
            url='https://api.open-meteo.com/v1/elevation?'+urllib.parse.urlencode({'latitude':','.join(str(l['lat']) for l in missing),'longitude':','.join(str(l['lon']) for l in missing)})
            with urllib.request.urlopen(url,timeout=60) as r:j=json.load(r)
            if len(j['elevation'])!=len(missing):raise ValueError('Elevation count mismatch')
            for l,v in zip(missing,j['elevation']):elevation[l['id']]={'elevation':v,'retrieved_at':out['generated_at'],'url':url,'resolution_m':90}
            ep.write_text(json.dumps(elevation,indent=2))
        except Exception as e:out['elevation_error']=str(e)
    for l in ls:
        j=json.loads((DATA/(l['id']+'.json')).read_text());df=pd.DataFrame(j['rows'],columns=j['columns']);stats={};hist={}
        df['date']=df['date'].astype(str);df['year']=pd.to_datetime(df.date,errors='coerce').dt.year;df['month']=pd.to_datetime(df.date,errors='coerce').dt.month
        for k in KEYS:
            s=pd.to_numeric(df[k],errors='coerce').dropna();stats[k]={'n':len(s),'mean':safe(s.mean()),'median':safe(s.median()),'std':safe(s.std()),'p95':safe(s.quantile(.95)),'min':safe(s.min()),'max':safe(s.max())}
            hist[k]=[]
            if len(s):
                counts,edges=np.histogram(s,bins=10)
                hist[k]=[{'label':f'{edges[i]:.1f}–{edges[i+1]:.1f}','count':int(v)} for i,v in enumerate(counts)]
        c=df[KEYS].corr(min_periods=30);correlations={k:{j:safe(c.loc[k,j]) for j in KEYS} for k in KEYS};counts={k:{j:int(df[[k,j]].notna().all(axis=1).sum()) for j in KEYS} for k in KEYS}
        monthly=[]
        for (y,m),b in df.groupby(['year','month'],dropna=True):
            valid=b[b.severity>=0]
            monthly.append({'year':int(y),'month':int(m),'rain_mean':safe(b.rain.mean()),'flow_mean':safe(b.q.mean()),'unusual_rate':safe(100*(valid.severity==2).mean()),'days':int(len(valid))})
        paired=df[['rain','q']].apply(pd.to_numeric,errors='coerce').dropna()
        if len(paired)>600:paired=paired.iloc[np.linspace(0,len(paired)-1,600).astype(int)]
        scatter=[{'rain':safe(row.rain),'flow':safe(row.q)} for row in paired.itertuples()]
        post_calendar=df[df.year>=2021]
        calendar=[{'date':row.date,'severity':int(row.severity) if pd.notna(row.severity) else -1} for row in post_calendar[['date','severity']].itertuples(index=False)]
        monsoons=[]
        for name,months in [('Southwest monsoon',[5,6,7,8,9]),('Northeast monsoon',[11,12,1]),('Inter-monsoon',[2,3,4,10])]:
            b=df[df.month.isin(months)];post=b[b.date>='2021-01-01'];valid=post.severity>=0
            monsoons.append({'season':name,'rain_days':int(b.rain.notna().sum()),'rain_mean':safe(b.rain.mean()),'flow_mean':safe(b.q.mean()),'unusual_rate':safe(100*(post.loc[valid,'severity']==2).mean())})
        years=[]
        for y,b in df[df.date>='2021-01-01'].groupby(df.date.str[:4]):
            valid=b.severity>=0;flow=b.qp.notna();years.append({'year':y,'days':int(valid.sum()),'unusual_days':int((b.severity==2).sum()),'rate':safe(100*(b.loc[valid,'severity']==2).mean()),'flow_days':int((b.qp>=99).sum()),'valid_flow_days':int(flow.sum()),'partial':b.date.min()!=y+'-01-01' or b.date.max()!=y+'-12-31'})
        last=df.iloc[-1];risk=risk_score(last,has_flow=l.get('flood_unique',0)>1)
        out['ranking'].append({'id':l['id'],'name':l['name'],'district':l.get('district',l['region']),'score':risk['score'],'basis':risk['basis'],'components':risk['components'],'weights':risk['weights'],'elevation':elevation.get(l['id'],{}).get('elevation'),'date':last.date})
        out['locations'][l['id']]={'statistics':stats,'histograms':hist,'correlations':correlations,'correlation_counts':counts,'monsoons':monsoons,'years':years,'monthly':monthly,'scatter':scatter,'calendar':calendar}
    out['ranking'].sort(key=lambda x:x['score'] if x['score'] is not None else -1,reverse=True)
    out['risk_method']={'scale':'0-100','weights':{'flood_severity':.50,'recent_cumulative_rainfall':.30,'unusual_weather':.20},'flood_component':'Monthly historical percentile of modelled river discharge; unavailable when the location has no usable flow variation.','rainfall_component':'Monthly historical percentile of 3-day cumulative rainfall.','weather_component':'Maximum of monthly historical percentiles for daily maximum temperature and wind speed.','fallback':'Unavailable components are omitted and the remaining weights are rescaled; the ranking basis identifies this explicitly.','interpretation':'Screening index, not a calibrated probability or official warning.'}
    (DATA/'eda.json').write_text(json.dumps(out,separators=(',',':'),allow_nan=False));print('EDA saved for',len(ls),'district reference points')
if __name__=='__main__':main()
