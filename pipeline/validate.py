"""Validate published daily records and recompute analytical fields independently."""
import json
import numpy as np
import pandas as pd
from config import DATA, COLUMNS, START
from analyze import derive, save

def main():
    summary=json.loads((DATA/'summary.json').read_text());expected=pd.date_range(START,summary['end']).strftime('%Y-%m-%d').tolist()
    assert len(summary['locations'])==25 and len({x['district'] for x in summary['locations']})==25
    assert summary['baseline_start']==START and summary['baseline_end']==summary['end']
    total=flow=0;missing={}
    for loc in summary['locations']:
        obj=json.loads((DATA/(loc['id']+'.json')).read_text());assert obj['columns']==COLUMNS
        frame=pd.DataFrame(obj['rows'],columns=obj['columns']);assert frame.date.tolist()==expected
        for key,lo,hi in [('rain',0,2000),('wind',0,500),('humidity',0,100),('temp',-90,65),('pressure',800,1100),('q',0,float('inf'))]:assert frame[key].dropna().between(lo,hi).all(),(loc['id'],key)
        rebuilt,_=derive(frame)
        for field in ['r3','r7','qp','rp','tp','wp','severity']:assert np.allclose(pd.to_numeric(frame[field]),pd.to_numeric(rebuilt[field]),equal_nan=True),field
        total+=len(frame);flow+=int(frame.q.notna().sum());missing[loc['id']]=int(frame.q.isna().sum())
    assert total==summary['daily_rows'] and flow==summary['flood_rows']
    assert len(json.loads((DATA/'districts.geojson').read_text())['features'])==25
    eda=json.loads((DATA/'eda.json').read_text());assert len(eda['locations'])==25
    for row in eda['ranking']:
        if row['score'] is not None:assert 0<=row['score']<=100
    current=json.loads((DATA/'current.json').read_text())
    for field in ['weather','flood']:
        for lid,item in current.get(field,{}).items():
            dates=item.get('daily',{}).get('time',[]);assert len(set(dates))==len(dates)
            for key,values in item.get('daily',{}).items():assert len(values)==len(dates),(field,lid,key)
    save(DATA/'validation.json',{'status':'passed','release_id':summary['release_id'],'archive_start':START,'archive_end':summary['end'],'daily_rows':total,'flood_rows':flow,'missing_flow_by_location':missing,'baseline':summary['baseline_period'],'checks':['25 unique districts','consecutive daily keys','physical ranges','full-archive percentile and rolling reconciliation','score bounds','forecast date alignment','25 geometry features'],'scope':'Published daily records; original hourly files not included in this release.'})
    print('PASS:',total,'daily records; full-archive analytics reconciled')
if __name__=='__main__':main()
