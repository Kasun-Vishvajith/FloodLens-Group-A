"""Convert unaggregated source records to compressed Parquet, preserving missing values.
Partitions district/year (hourly) and district/date (daily) avoid excessive tiny hourly files.
"""
import json
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parents[1]
def main():
    ls=json.loads((ROOT/'pipeline/locations.json').read_text());out=ROOT/'data/parquet';files=rows=0
    for l in ls:
        for p in (ROOT/'data/processed-v2/hourly').glob(f"year=*/{l['id']}.csv.gz"):
            df=pd.read_csv(p);df['district']=l['district'];df['time']=pd.to_datetime(df.time);df['date']=df.time.dt.strftime('%Y-%m-%d');year=p.parent.name
            dest=out/'raw-hourly'/('district='+l['district'].replace(' ','_'))/year;dest.mkdir(parents=True,exist_ok=True)
            pq.write_table(pa.Table.from_pandas(df,preserve_index=False),dest/'part.parquet',compression='zstd',coerce_timestamps='us',allow_truncated_timestamps=False);files+=1;rows+=len(df)
        source=ROOT/'data/processed-v2'/f"daily-{l['id']}.csv.gz"
        df=pd.read_csv(source);df['district']=l['district']
        # Daily/date partitioning is selectable in Spark for S3 publication; compact local source per district.
        dest=out/'raw-daily'/('district='+l['district'].replace(' ','_'));dest.mkdir(parents=True,exist_ok=True)
        pq.write_table(pa.Table.from_pandas(df,preserve_index=False),dest/'part.parquet',compression='zstd',coerce_timestamps='us',allow_truncated_timestamps=False)
    metadata={'hourly_rows':rows,'hourly_files':files,'compression':'zstd','hourly_partitions':['district','year'],'daily_partitions':['district'],'bytes':sum(p.stat().st_size for p in out.rglob('*.parquet'))}
    (ROOT/'dist/data/parquet-manifest.json').write_text(json.dumps(metadata,indent=2));print(metadata)
if __name__=='__main__':main()
