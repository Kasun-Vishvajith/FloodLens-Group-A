"""Optional local Spark verification of full-archive published analytics.
Requires Java 17 and pyspark==3.5.6. No Databricks or cloud account.
"""
import json,time
from pathlib import Path
from config import ROOT,DATA

def main():
    from pyspark.sql import SparkSession,functions as F,Window
    started=time.perf_counter()
    spark=SparkSession.builder.master('local[2]').appName('FloodLens verification').config('spark.driver.memory','2g').config('spark.sql.shuffle.partitions','8').getOrCreate()
    try:
        raw=spark.read.option('header',True).option('inferSchema',True).csv(str(DATA/'historical-daily.csv'))
        frame=raw.withColumn('date',F.to_date('date')).withColumn('month',F.month('date')).withColumn('day',F.datediff('date',F.lit('1970-01-01')))
        for n in [3,7]:
            win=Window.partitionBy('location_id').orderBy('day').rangeBetween(-(n-1),0)
            frame=frame.withColumn('check_r'+str(n),F.when(F.count('rain').over(win)==n,F.round(F.sum('rain').over(win),6)))
        reference=frame.groupBy('location_id','month').agg(*[F.collect_list(k).alias(k+'_reference') for k in ['q','r3','tmax','wind']])
        frame=frame.join(reference,['location_id','month'])
        for key,target in [('q','qp'),('r3','rp'),('tmax','tp'),('wind','wp')]:
            expression=f'100.0*(size(filter({key}_reference,x -> x < {key}))+0.5*size(filter({key}_reference,x -> x = {key})))/size({key}_reference)'
            frame=frame.withColumn('check_'+target,F.when(F.col(key).isNotNull()&(F.size(key+'_reference')>=30),F.expr(expression)))
        for key in ['r3','r7','qp','rp','tp','wp']:
            mismatch=frame.filter((F.col(key).isNull()!=F.col('check_'+key).isNull()) | (F.abs(F.col(key)-F.col('check_'+key))>0.00001)).count()
            assert mismatch==0,(key,mismatch)
        count=frame.count();summary=json.loads((DATA/'summary.json').read_text());assert count==summary['daily_rows']
        report={'status':'passed','release_id':summary['release_id'],'daily_rows':count,'seconds':time.perf_counter()-started,'spark_version':spark.version,'execution':'local[2]','scope':'Recompute rolling rainfall and monthly percentile ranks from published daily CSV; no hourly or distributed-cluster claim.'}
        (ROOT/'docs/SPARK_VALIDATION.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
    finally:spark.stop()
if __name__=='__main__':main()
