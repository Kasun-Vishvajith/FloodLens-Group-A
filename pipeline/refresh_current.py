"""Save a timestamped live forecast snapshot for the static dashboard."""
import datetime as dt,json,urllib.request,urllib.parse,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def get(url):
    with urllib.request.urlopen(url,timeout=60) as r:
        j=json.load(r)
    if isinstance(j,dict) and j.get('error'):raise RuntimeError(j.get('reason'))
    return j if isinstance(j,list) else [j]
def main():
    ls=json.loads((ROOT/'pipeline/locations.json').read_text());out={'origin':'Saved API snapshot','retrieved_at':dt.datetime.now(dt.timezone.utc).isoformat(),'weather':{},'flood':{},'weather_at':{},'flood_at':{}}
    previous=ROOT/'dist/data/current.json'
    if previous.exists():
        saved=json.loads(previous.read_text(encoding='utf-8'))
        out['flood']=saved.get('flood',{})
        out['flood_at']={key:saved.get('flood_at',{}).get(key,saved.get('retrieved_at')) for key in out['flood']}
    p=dict(latitude=','.join(str(x['lat']) for x in ls),longitude=','.join(str(x['lon']) for x in ls),current='temperature_2m,relative_humidity_2m,wind_speed_10m,pressure_msl',daily='temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max,precipitation_probability_max',timezone='GMT',forecast_days=16)
    w=get('https://api.open-meteo.com/v1/forecast?'+urllib.parse.urlencode(p))
    if len(w)!=len(ls):raise ValueError('Weather response location count mismatch')
    for l,j in zip(ls,w):out['weather'][l['id']]=j;out['weather_at'][l['id']]=out['retrieved_at']
    rivers=[l for l in ls if l['river']]
    fp=dict(latitude=','.join(str(x['lat']) for x in rivers),longitude=','.join(str(x['lon']) for x in rivers),daily='river_discharge_median,river_discharge_p25,river_discharge_p75',forecast_days=16,models='forecast_v4')
    try:
        f=get('https://flood-api.open-meteo.com/v1/flood?'+urllib.parse.urlencode(fp))
        if len(f)!=len(rivers):raise ValueError('Flood response location count mismatch')
        for l,j in zip(rivers,f):out['flood'][l['id']]=j;out['flood_at'][l['id']]=out['retrieved_at']
    except Exception as e:out['flood_error']=str(e);print('Flood forecast unavailable:',e)
    (ROOT/'dist/data').mkdir(exist_ok=True,parents=True)
    (ROOT/'dist/data/current.json').write_text(json.dumps(out,separators=(',',':')))
    with (ROOT/'dist/data/forecast-daily.csv').open('w',newline='') as file:
        writer=csv.writer(file);writer.writerow(['location_id','date_utc','temperature_max_c','temperature_min_c','precipitation_mm','wind_max_kmh','rain_probability_max_pct','flow_median_m3s','flow_p25_m3s','flow_p75_m3s','retrieved_utc'])
        for l in ls:
            d=out['weather'][l['id']]['daily'];fd=out['flood'].get(l['id'],{}).get('daily',{});fdates=fd.get('time',[])
            for i,date in enumerate(d['time']):
                fi=fdates.index(date) if date in fdates else -1
                flows=[fd.get(k,[])[fi] if fi>=0 else None for k in ['river_discharge_median','river_discharge_p25','river_discharge_p75']]
                writer.writerow([l['id'],date,*[d.get(k,[None]*len(d['time']))[i] for k in ['temperature_2m_max','temperature_2m_min','precipitation_sum','wind_speed_10m_max','precipitation_probability_max']],*flows,out['retrieved_at']])
    print(f"Saved weather for {len(w)} locations and flow forecasts for {len(out['flood'])} locations")
if __name__=='__main__':main()
