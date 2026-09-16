"""Run the same Databricks notebook locally for an independently reproducible Spark check.
Requires Java 17 and pyspark==3.5.6. Databricks itself is not required for this check.
"""
from pathlib import Path
import json,time
from pyspark.sql import SparkSession
ROOT=Path(__file__).resolve().parents[1]
class Widgets:
    def __init__(self):self.values={'input_path':str(ROOT/'data/parquet/raw-hourly'),'flow_path':str(ROOT/'data/parquet/raw-daily'),'output_path':str(ROOT/'data/spark-output'),'raw_date_partitions':'false'}
    def text(self,*args):pass
    def dropdown(self,*args):pass
    def get(self,key):return self.values[key]
class Utils:widgets=Widgets()
started=time.perf_counter()
spark=SparkSession.builder.master('local[2]').appName('FloodLens-Group-A-Validation').config('spark.driver.memory','2g').config('spark.sql.shuffle.partitions','8').config('spark.sql.session.timeZone','UTC').getOrCreate()
namespace={'spark':spark,'dbutils':Utils(),'display':lambda frame:frame.show(6,truncate=False)}
# Local validation uses compact output partitioning to avoid 97,000 tiny files.
source=(ROOT/'pipeline/databricks_spark.py').read_text().replace("partitionBy('district','date').parquet(destination+'/daily')","partitionBy('district').parquet(destination+'/daily')")
try:
    exec(compile(source,'databricks_spark.py','exec'),namespace)
    frame=spark.read.parquet(str(ROOT/'data/spark-output/daily'));n=frame.count()
    expected=json.loads((ROOT/'dist/data/summary.json').read_text())['daily_rows'];assert n==expected,(n,expected)
    assert frame.select('location_id','date').distinct().count()==n
    report={'status':'passed','spark_version':spark.version,'master':'local[2]','driver_memory':'2g','daily_rows':n,'elapsed_seconds':time.perf_counter()-started,'cloud_execution':False,'output_partitioning':'district (local validation; notebook supports district/date)'}
    (ROOT/'dist/data/spark-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
finally:spark.stop()
