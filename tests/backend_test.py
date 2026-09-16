"""Actual HTTP smoke tests against the packaged FastAPI backend; no cloud writes."""
import json,subprocess,sys,time,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=subprocess.Popen([sys.executable,'-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8766'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
def get(path):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8766'+path,timeout=10) as r:return r.status,json.load(r)
    except urllib.error.HTTPError as e:return e.code,json.load(e)
try:
    for i in range(50):
        try:
            status,j=get('/api/health');break
        except urllib.error.URLError:time.sleep(.1)
    assert status==200 and j['storage']=='packaged JSON'
    status,j=get('/api/history/hanwella?start=2026-09-01&end=2026-09-07');assert status==200 and len(j['records'])==7
    assert get('/api/history/unknown')[0]==404
    assert get('/api/history/hanwella?start=2026-09-07&end=2026-09-01')[0]==422
    assert get('/api/place?latitude=95&longitude=80')[0]==422
    status,j=get('/api/compact-history/hanwella');assert status==200 and len(j['columns'])==17 and j['rows'][0][0]=='2016-01-01'
    assert get('/api/assets/secret.json')[0]==404
    print('PASS: backend HTTP routes, date filtering, unknown locations, coordinate bounds, compact schema, asset allowlist')
finally:
    p.terminate();p.wait(timeout=10)
