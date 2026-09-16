"""Validate the published archive against its requested coverage and source data."""
import json,sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def main():
    s=json.loads((ROOT/'dist/data/summary.json').read_text());count=0;missing={}
    expected=pd.date_range(s['start'],s['end'],freq='D').strftime('%Y-%m-%d').tolist()
    assert s['start']=='2016-01-01'
    assert len(s['locations'])==25
    assert len({l['district'] for l in s['locations']})==25
    assert pd.Timestamp(s['end'])<pd.Timestamp(s['as_of'])
    for l in s['locations']:
        j=json.loads((ROOT/'dist/data'/f"{l['id']}.json").read_text());d=pd.DataFrame(j['rows'],columns=j['columns'])
        assert d.date.tolist()==expected, f"Nonconsecutive dates: {l['id']}"
        assert not d.date.duplicated().any()
        raw=pd.read_csv(ROOT/'data/processed-v2'/f"daily-{l['id']}.csv.gz")
        assert np.allclose(d.rain,raw.rain,equal_nan=True)
        assert np.allclose(d.r3,raw.rain.rolling(3,min_periods=3).sum(),equal_nan=True)
        assert np.allclose(d.r7,raw.rain.rolling(7,min_periods=7).sum(),equal_nan=True)
        for v in ['rain','wind','q']:assert (d[v].dropna()>=0).all(),f'Negative {v}'
        assert d.humidity.dropna().between(0,100).all()
        assert d.temp.dropna().between(-90,65).all()
        assert d.pressure.dropna().between(800,1100).all()
        assert d.wind.dropna().between(0,500).all()
        assert d.rain.dropna().between(0,2000).all()
        for v in ['rp','qp','tp','wp']:assert d[v].dropna().between(0,100).all()
        assert set(d.weather_model.dropna()).issubset({'ERA5','ECMWF IFS recent'})
        assert not d.loc[d.date<'2017-01-01','weather_model'].eq('ECMWF IFS recent').any()
        count+=len(d);missing[l['id']]={k:int(d[k].isna().sum()) for k in ['rain','temp','humidity','wind','pressure','q']}
    assert count==s['daily_rows'];assert s['hourly_rows']==count*24
    assert len(json.loads((ROOT/'dist/data/districts.geojson').read_text())['features'])==25
    snapshot=json.loads((ROOT/'dist/data/current.json').read_text())
    assert set(snapshot['weather'])=={l['id'] for l in s['locations']}
    for w in snapshot['weather'].values():
        assert len(w['daily']['time'])==16
        assert len(set(w['daily']['time']))==16
    # A missing forecast is surfaced; historical completeness does not imply live availability.
    forecast_missing=sum(not any(v is not None for v in snapshot.get('flood',{}).get(l['id'],{}).get('daily',{}).get('river_discharge_median',[])) for l in s['locations'])
    result={'status':'passed','archive_start':s['start'],'archive_end':s['end'],'as_of':s['as_of'],'hourly_rows':s['hourly_rows'],'daily_rows':count,'missing_by_location':missing,'missing_flood_forecast_locations':forecast_missing,'map_districts':25,'checks':['consecutive dates','unique keys','physical ranges','source labels','percentile bounds','forecast location coverage','district geometry count','25 unique district reference points','16 forecast dates','source rainfall reconciliation','rolling accumulation reconciliation']}
    (ROOT/'dist/data/validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
