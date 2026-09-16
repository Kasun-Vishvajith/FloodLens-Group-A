"""Check that independently executed Spark results agree with dashboard analytics."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
spark=pd.read_parquet(ROOT/'data/spark-output/daily');spark['date']=pd.to_datetime(spark.date).dt.strftime('%Y-%m-%d');frames=[]
for l in json.loads((ROOT/'dist/data/summary.json').read_text())['locations']:
    j=json.loads((ROOT/'dist/data'/f"{l['id']}.json").read_text());d=pd.DataFrame(j['rows'],columns=j['columns']);d['location_id']=l['id'];frames.append(d)
web=pd.concat(frames);m=spark.merge(web,on=['location_id','date'],suffixes=('_spark','_web'),validate='one_to_one')
assert len(m)==len(web)==len(spark)
fields=['rain','temp','humidity','wind','pressure','q','r3','r7','qp','rp','tp','wp','severity']
for k in fields:assert np.allclose(pd.to_numeric(m[k+'_spark']),pd.to_numeric(m[k+'_web']),equal_nan=True,rtol=1e-9,atol=1e-9),k
p=ROOT/'dist/data/spark-validation.json';j=json.loads(p.read_text());j['pandas_reconciliation']={'rows':len(m),'fields':fields,'status':'passed'};p.write_text(json.dumps(j,indent=2))
print('PASS: Spark and dashboard agree across',len(m),'rows and',len(fields),'analytical fields')
