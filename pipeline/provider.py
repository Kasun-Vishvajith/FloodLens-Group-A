"""Serial, cached API requests with quota estimates, retries and attempt logging."""
import datetime as dt
import email.utils
import gzip
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from config import ROOT

class Client:
    def __init__(self, run_id, cache_dir=None):
        self.run_id = run_id
        self.cache_dir = Path(cache_dir or ROOT / 'data/raw')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log = ROOT / 'data/request-log.jsonl'
        self.log.parent.mkdir(exist_ok=True)
        self.events = []
        self.window = []
        self.day_units = 0
        today=dt.datetime.now(dt.timezone.utc).date()
        if self.log.exists():
            for line in self.log.read_text().splitlines():
                try:
                    event=json.loads(line);stamp=dt.datetime.fromisoformat(event['utc']);units=event.get('estimated_units',0)
                    if stamp.date()==today:self.day_units+=units
                    if time.time()-stamp.timestamp()<3600:self.window.append((stamp.timestamp(),units))
                except (ValueError,KeyError):continue

    def record(self, event):
        event.update(run_id=self.run_id, utc=dt.datetime.now(dt.timezone.utc).isoformat())
        self.events.append(event)
        with self.log.open('a') as stream:
            stream.write(json.dumps(event) + '\n')

    def get(self, endpoint, params, cache_seconds=0):
        url = endpoint + '?' + urllib.parse.urlencode(params)
        key = hashlib.sha256(url.encode()).hexdigest()
        path = self.cache_dir / (key + '.json.gz')
        if path.exists() and time.time() - path.stat().st_mtime < cache_seconds:
            with gzip.open(path, 'rt') as stream:
                result = json.load(stream)
            self.record(dict(endpoint=endpoint,url_hash=key,cache_hit=True,estimated_units=0))
            return result
        points = len(str(params.get('latitude', '0')).split(','))
        days = int(params.get('forecast_days', 1))
        if 'start_date' in params:
            days = (dt.date.fromisoformat(params['end_date'])-dt.date.fromisoformat(params['start_date'])).days+1
        units = max(1,days/14)*points
        if units > 550:
            raise ValueError('Split request into smaller coordinate/date batches')
        for attempt in range(1,6):
            if self.day_units + units > 8000:
                raise RuntimeError('Conservative run quota reached; resume in a later quota window')
            while True:
                now = time.time()
                self.window = [(t,u) for t,u in self.window if now-t < 3600]
                if sum(u for t,u in self.window if now-t<60)+units<=550 and sum(u for t,u in self.window)+units<=4500:
                    break
                time.sleep(10)
            self.window.append((time.time(),units));self.day_units += units
            start=time.perf_counter();error=None
            try:
                with urllib.request.urlopen(url, timeout=60) as response:
                    body=response.read();value=json.loads(body)
                if isinstance(value,dict) and value.get('error'):
                    raise ValueError(value.get('reason','Provider rejected query'))
                result={'url':url,'retrieved_at':dt.datetime.now(dt.timezone.utc).isoformat(),'response':value}
                with gzip.open(path,'wt') as stream:json.dump(result,stream)
                self.record(dict(endpoint=endpoint,url_hash=key,attempt=attempt,cache_hit=False,status=200,estimated_units=units,seconds=time.perf_counter()-start,bytes=len(body)))
                return result
            except (urllib.error.URLError,TimeoutError,ValueError) as exc:
                error=exc
                code=getattr(exc,'code',None)
                self.record(dict(endpoint=endpoint,url_hash=key,attempt=attempt,cache_hit=False,status=code,error=type(exc).__name__,estimated_units=units,seconds=time.perf_counter()-start))
                if attempt==5 or (code is not None and code not in [429,500,502,503,504]):raise
                retry=getattr(exc,'headers',{}).get('Retry-After','') if getattr(exc,'headers',None) else ''
                try:delay=float(retry)
                except ValueError:
                    try:delay=email.utils.parsedate_to_datetime(retry).timestamp()-time.time()
                    except (ValueError,TypeError):delay=2**attempt
                if delay>300:raise RuntimeError('Provider asks for a long pause; preserve old release and retry later') from exc
                time.sleep(max(2**attempt,delay))
