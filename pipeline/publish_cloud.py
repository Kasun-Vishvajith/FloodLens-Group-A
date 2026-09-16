"""Explicit cloud writes: python pipeline/publish_cloud.py --s3 --postgres.
AWS and PostgreSQL credentials come from environment / normal AWS profile.
"""
import argparse,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--s3',action='store_true');p.add_argument('--postgres',action='store_true');p.add_argument('--spark-daily',help='Downloaded Spark processed daily Parquet directory');a=p.parse_args()
    if a.s3:
        import boto3
        bucket=os.environ['S3_BUCKET'];client=boto3.client('s3')
        files=list((ROOT/'data/parquet').rglob('*.parquet'))
        if not files:raise RuntimeError('Run export_parquet.py first')
        for f in files:client.upload_file(str(f),bucket,'floodlens/'+f.relative_to(ROOT/'data/parquet').as_posix())
        print('Uploaded',len(files),'Parquet objects')
    if a.postgres:
        import psycopg
        with psycopg.connect(os.environ['DATABASE_URL']) as conn:
            conn.execute((ROOT/'infra/schema.sql').read_text())
            locations=json.loads((ROOT/'dist/data/summary.json').read_text())['locations']
            for l in locations:
                j=json.loads((ROOT/'dist/data'/f"{l['id']}.json").read_text());columns=['location_id']+j['columns']
                if a.spark_daily:
                    import pandas as pd
                    spark=pd.read_parquet(a.spark_daily,filters=[('location_id','=',l['id'])]);spark=spark.sort_values('date')
                    if spark.duplicated(['location_id','date']).any():raise ValueError('Duplicate Spark keys')
                    values=spark[j['columns']].astype(object).where(pd.notna(spark[j['columns']]),None)
                    j['rows']=values.values.tolist()
                # All identifiers are package-owned, not request input.
                allowed={'location_id','date','rain','temp','humidity','wind','pressure','tmax','q','r3','r7','qp','rp','tp','wp','severity','weather_model','flow_source'}
                if set(columns)!=allowed:raise ValueError('Unexpected data schema')
                sql='INSERT INTO daily_weather ('+','.join(columns)+') VALUES ('+','.join(['%s']*len(columns))+') ON CONFLICT (location_id,date) DO UPDATE SET '+','.join(c+'=EXCLUDED.'+c for c in columns if c not in ['date','location_id'])
                with conn.cursor() as cur:cur.executemany(sql,[[l['id']]+r for r in j['rows']])
                print('Loaded',l['id'],len(j['rows']))
if __name__=='__main__':main()
