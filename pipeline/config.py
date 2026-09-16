"""One source of truth for paths, fields and analytical policy."""
from pathlib import Path
import os
ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get('FLOODLENS_DATA', ROOT / 'public/data'))
START = '2016-01-01'
VARIABLES = ['precipitation','temperature_2m','relative_humidity_2m','wind_speed_10m','pressure_msl']
COLUMNS = ['date','rain','temp','humidity','wind','pressure','tmax','q','r3','r7','qp','rp','tp','wp','severity','weather_model','flow_source']
RAW_COLUMNS = ['date','rain','temp','humidity','wind','pressure','tmax','q','weather_model','flow_source']
