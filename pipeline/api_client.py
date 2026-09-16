"""Open-Meteo API client with resumable cache, retries and a conservative quota ledger.

Caches original responses, retains provenance, writes one hourly Parquet file per
location/year. Serial downloads cap memory. Failed requests never become zeros.
"""
import argparse, datetime as dt, gzip, hashlib, json, math, time
import urllib.request, urllib.parse, urllib.error
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
OUT = ROOT / 'data/processed'
VARIABLES = ['precipitation', 'temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'pressure_msl']

def fetch(url, budget=8500):
    RAW.mkdir(parents=True, exist_ok=True)
    cache = RAW / (hashlib.sha256(url.encode()).hexdigest() + '.json.gz')
    if cache.exists():
        with gzip.open(cache, 'rt') as f: return json.load(f)
    p = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    days = (dt.date.fromisoformat(p['end_date'][0])-dt.date.fromisoformat(p['start_date'][0])).days+1
    # Conservative planning estimate: do not discount calls for fewer variables.
    cost = max(1, days/14) * len(p.get('latitude',['0'])[0].split(','))
    ledger_path = RAW/'quota-ledger.json'
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
    if cost>580:
        raise ValueError('Date range exceeds a single-request quota allowance; use a shorter collection interval.')
    windows_path=RAW/'quota-windows.json'
    windows=json.loads(windows_path.read_text()) if windows_path.exists() else []
    for attempt in range(5):
        while True:
            today=dt.datetime.now(dt.timezone.utc).date().isoformat()
            if ledger.get(today,0)+cost>budget:
                raise RuntimeError('Conservative daily API budget reached; resume tomorrow.')
            now=time.time();windows=json.loads(windows_path.read_text()) if windows_path.exists() else [];windows=[x for x in windows if now-x[0]<3600]
            ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
            minute=sum(x[1] for x in windows if now-x[0]<60)
            hour=sum(x[1] for x in windows)
            if minute+cost<=580 and hour+cost<=4800:break
            print('Waiting for rolling API quota; cached work is safe.',flush=True)
            time.sleep(30)
        # Reserve every attempt, including retries, before network access.
        windows.append([time.time(),cost]);windows_path.write_text(json.dumps(windows))
        ledger[today]=ledger.get(today,0)+cost;ledger_path.write_text(json.dumps(ledger,indent=2))
        try:
            with urllib.request.urlopen(url, timeout=100) as r: body = json.load(r)
            if isinstance(body,dict) and body.get('error'): raise ValueError(body.get('reason'))
            wrapped={'url':url,'retrieved_at':dt.datetime.now(dt.timezone.utc).isoformat(),'response':body}
            with gzip.open(cache, 'wt') as f: json.dump(wrapped,f,separators=(',',':'))
            return wrapped
        except urllib.error.HTTPError as e:
            if e.code not in (429,500,502,503,504): raise
            delay=min(60, max(int(e.headers.get('Retry-After','0') or 0),2**attempt*5))
            print(f'HTTP {e.code}; retry in {delay}s',flush=True);time.sleep(delay)
        except (TimeoutError,urllib.error.URLError):
            if attempt==4: raise
            time.sleep(min(30,2**attempt*2))
    raise RuntimeError('API retries exhausted. Resume with the same command.')

