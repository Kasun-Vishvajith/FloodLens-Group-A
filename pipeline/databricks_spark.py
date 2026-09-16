# Databricks notebook source
# Upload data/parquet to a Unity Catalog Volume in Databricks Free Edition.
# External S3/RDS connections depend on account/network permissions. This notebook
# also accepts accessible s3:// paths in a configured paid/student workspace.
# No forecasting model is fitted.
from pyspark.sql import functions as F, Window

dbutils.widgets.text('input_path','/Volumes/workspace/default/floodlens/raw-hourly')
dbutils.widgets.text('output_path','/Volumes/workspace/default/floodlens/processed')
dbutils.widgets.dropdown('raw_date_partitions','false',['false','true'])
dbutils.widgets.text('flow_path','/Volumes/workspace/default/floodlens/raw-daily')
spark.conf.set('spark.sql.session.timeZone','UTC')
source=dbutils.widgets.get('input_path');destination=dbutils.widgets.get('output_path')
raw=spark.read.option('mergeSchema','true').parquet(source)
if dbutils.widgets.get('raw_date_partitions')=='true':
    # Exact proposal partitioning; many small files for a district-point dataset.
    raw.write.mode('overwrite').partitionBy('district','date').parquet(destination+'/raw-by-date')
required=['location_id','time','district','temperature_2m','relative_humidity_2m','precipitation','wind_speed_10m','pressure_msl']
assert all(c in raw.columns for c in required),'Required columns missing'
clean=raw.withColumn('time',F.to_timestamp('time')).filter(F.col('time').isNotNull()).dropDuplicates(['location_id','time'])
# Physical validity: flag missing/invalid records; do not interpolate extreme events.
for column,low,high in [('relative_humidity_2m',0,100),('precipitation',0,2000),('wind_speed_10m',0,500),('temperature_2m',-90,65),('pressure_msl',800,1100)]:
    clean=clean.withColumn(column,F.when(F.col(column).between(low,high),F.col(column)).otherwise(F.lit(None).cast('double')))
clean=clean.withColumn('date',F.to_date('time'))
metrics=[('precipitation','rain','sum'),('temperature_2m','temp','avg'),('relative_humidity_2m','humidity','avg'),('wind_speed_10m','wind','max'),('pressure_msl','pressure','avg')]
expr=[]
for source_col,target,fn in metrics:
    expr.append(F.when(F.count(source_col)==24,getattr(F,fn)(source_col)).alias(target))
daily=clean.groupBy('location_id','district','date').agg(*expr,F.when(F.count('temperature_2m')==24,F.max('temperature_2m')).alias('tmax'),F.count('*').alias('hours'),F.first('weather_model',ignorenulls=True).alias('weather_model'))
daily=daily.withColumn('rain',F.round('rain',6))
flows=spark.read.parquet(dbutils.widgets.get('flow_path')).select('location_id',F.to_date('date').alias('date'),'q','flow_source').dropDuplicates(['location_id','date'])
daily=daily.join(flows,['location_id','date'],'left').withColumn('month',F.month('date'))
# Calendar-aware windows: gaps are not compressed into adjacent days.
daily=daily.withColumn('day_number',F.datediff('date',F.lit('1970-01-01')))
for n in [3,7]:
    w=Window.partitionBy('location_id').orderBy('day_number').rangeBetween(-(n-1),0)
    daily=daily.withColumn('r'+str(n),F.when(F.count('rain').over(w)==n,F.round(F.sum('rain').over(w),6)))
baseline=daily.filter((F.col('date')>='2016-01-01')&(F.col('date')<'2021-01-01')).groupBy('location_id','month').agg(F.percentile_approx('q',.99,10000).alias('q99'),F.percentile_approx('r3',.99,10000).alias('r3_99'),F.count('q').alias('q_n'),F.count('r3').alias('rain_n'))
flagged=daily.join(baseline,['location_id','month'],'left').withColumn('unusual_flow',F.when((F.col('q_n')>=30)&(F.col('q99')>0),F.col('q')>=F.col('q99'))).withColumn('unusual_rain',F.when((F.col('rain_n')>=30)&(F.col('r3_99')>0),F.col('r3')>=F.col('r3_99')))
# Exact midrank percentiles match the dashboard definition (including ties).
reference=daily.filter((F.col('date')>='2016-01-01')&(F.col('date')<'2021-01-01')).groupBy('location_id','month').agg(*[F.collect_list(k).alias(k+'_reference') for k in ['q','r3','tmax','wind']])
flagged=flagged.join(reference,['location_id','month'],'left')
for k,target in [('q','qp'),('r3','rp'),('tmax','tp'),('wind','wp')]:
    expr=f"100.0 * (size(filter({k}_reference, x -> x < {k})) + 0.5 * size(filter({k}_reference, x -> x = {k}))) / size({k}_reference)"
    flagged=flagged.withColumn(target,F.when(F.col(k).isNotNull()&(F.size(k+'_reference')>0),F.expr(expr)))
peak=F.greatest('qp','rp','tp','wp')
flagged=flagged.withColumn('severity',F.when(peak>=99,2).when(peak>=95,1).when(peak.isNotNull(),0).otherwise(-1)).drop(*[k+'_reference' for k in ['q','r3','tmax','wind']])
flagged.write.mode('overwrite').partitionBy('district','date').parquet(destination+'/daily')
seasonal=flagged.withColumn('season',F.when(F.col('month').isin(5,6,7,8,9),'Southwest').when(F.col('month').isin(11,12,1),'Northeast').otherwise('Inter-monsoon')).groupBy('district','season').agg(F.avg('rain').alias('mean_daily_rain_mm'),F.avg('q').alias('mean_flow_m3s'),F.count('rain').alias('valid_rain_days'))
seasonal.write.mode('overwrite').parquet(destination+'/seasonal')
display(seasonal.orderBy('district','season'))
# Approximate Spark quantiles can differ slightly from the exact local pandas baseline.
# Capture real Spark job runtimes and screenshots for the report after running this notebook.

# Optional PostgreSQL/RDS output, only in a workspace with permitted JDBC network access.
# Create infra/schema.sql first. Store the JDBC URL/user/password in a Databricks secret scope.
# Use an append-only staging table, then the SQL below to upsert atomically from a trusted client.
# columns=['location_id','date','rain','temp','humidity','wind','pressure','tmax','q','r3','r7','qp','rp','tp','wp','severity','weather_model','flow_source']
# (flagged.select(*columns).write.format('jdbc')
#  .option('url',dbutils.secrets.get('floodlens','jdbc_url'))
#  .option('dbtable','daily_weather_staging')
#  .option('user',dbutils.secrets.get('floodlens','db_user'))
#  .option('password',dbutils.secrets.get('floodlens','db_password'))
#  .option('driver','org.postgresql.Driver').mode('overwrite').save())
