"""Run the incremental daily pipeline sequentially with a single-writer lock."""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    status_dir = ROOT / 'data'
    status_dir.mkdir(exist_ok=True)
    lock = status_dir / '.daily-refresh.lock'
    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise SystemExit('Refresh already locked. Check the recorded PID before removing a stale lock.')
    os.write(handle, str(os.getpid()).encode())
    os.close(handle)
    report = {'started_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'status': 'running'}
    def save():
        target = status_dir / 'refresh-status.json'
        temporary = target.with_suffix('.tmp')
        temporary.write_text(json.dumps(report, indent=2), encoding='utf-8')
        temporary.replace(target)
    try:
        for stage in ['ingest_v2.py', 'analyze.py', 'refresh_current.py', 'eda.py', 'validate_v2.py']:
            report['stage'] = stage
            save()
            subprocess.run([sys.executable, str(ROOT / 'pipeline' / stage)], cwd=ROOT, check=True)
        summary = json.loads((ROOT / 'dist/data/summary.json').read_text(encoding='utf-8'))
        report.update(status='complete', archive_end=summary['end'])
    except Exception as error:
        report.update(status='failed', error=str(error))
        raise
    finally:
        report['finished_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
        save()
        lock.unlink()

if __name__ == '__main__':
    main()
