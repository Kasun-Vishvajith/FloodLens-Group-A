"""Optional serial multi-coordinate backfill cache. Run before ingest_v2.py, not concurrently."""
import datetime as dt,json,gzip,hashlib,urllib.parse
import pandas as pd
from pathlib import Path
from api_client import fetch,VARIABLES,RAW
ROOT=Path(__file__).resolve().parents[1]
def main():
    ls=json.loads((ROOT/'pipeline/locations.json').read_text())
    def needs(l,kind):
        p=ROOT/'data/processed-v2'/f"daily-{l['id']}.csv.gz"
        return not p.exists() or (kind=='flood' and l['river'] and pd.read_csv(p).q.notna().sum()==0)
    today=dt.datetime.now(dt.timezone.utc).date();end=today-dt.timedelta(days=1);era=today-dt.timedelta(days=7)
    if not ls:return
    for kind in ['weather','flood']:
        group=[l for l in ls if (kind=='weather' or l['river']) and needs(l,kind)]
        if not group:continue
        for year in range(2016,end.year+1):
            left=dt.date(year,1,1);right=min(dt.date(year,12,31),era if kind=='weather' else end)
            pieces=[(left,right,'era5')] if kind=='weather' else [(left,right,None)]
            if kind=='weather' and year==end.year:pieces.append((era+dt.timedelta(days=1),end,'ecmwf_ifs'))
            for a,b,model in pieces:
                base={'start_date':a.isoformat(),'end_date':b.isoformat()}
                if kind=='weather':base.update(hourly=','.join(VARIABLES),models=model,timezone='GMT',wind_speed_unit='kmh');host='https://archive-api.open-meteo.com/v1/archive?'
                else:base.update(daily='river_discharge');host='https://flood-api.open-meteo.com/v1/flood?'
                # Match the ingestion URL's stable parameter order for reusable single-location cache entries.
                def params(l):return {'latitude':l['lat'],'longitude':l['lon'],**base}
                urls=[host+urllib.parse.urlencode(params(l)) for l in group]
                pending=[(l,u) for l,u in zip(group,urls) if not (RAW/(hashlib.sha256(u.encode()).hexdigest()+'.json.gz')).exists()]
                if not pending:continue
                selected,urls=map(list,zip(*pending))
                batch={'latitude':','.join(str(l['lat']) for l in selected),'longitude':','.join(str(l['lon']) for l in selected),**base};url=host+urllib.parse.urlencode(batch)
                raw=fetch(url);responses=raw['response'] if isinstance(raw['response'],list) else [raw['response']]
                if len(responses)!=len(selected):raise ValueError('Batch location count mismatch')
                for u,r in zip(urls,responses):
                    wrapped={'url':u,'batch_source_url':url,'retrieved_at':raw['retrieved_at'],'response':r}
                    with gzip.open(RAW/(hashlib.sha256(u.encode()).hexdigest()+'.json.gz'),'wt') as f:json.dump(wrapped,f,separators=(',',':'))
                print(kind,a,b,len(selected),'locations cached',flush=True)
if __name__=='__main__':main()
