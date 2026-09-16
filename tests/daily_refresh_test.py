"""Offline checks for daily sequencing, failures and lock cleanup."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('daily',Path(__file__).resolve().parents[1]/'pipeline/refresh_daily.py')
daily=importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily)

class DailyRefreshTest(unittest.TestCase):
    def test_sequence_and_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'dist/data').mkdir(parents=True)
            (root/'dist/data/summary.json').write_text('{"end":"2026-09-15"}')
            with patch.object(daily,'ROOT',root),patch.object(daily.subprocess,'run') as run:
                daily.main()
            self.assertEqual([Path(c.args[0][1]).name for c in run.call_args_list],['ingest_v2.py','analyze.py','refresh_current.py','eda.py','validate_v2.py'])
            self.assertEqual(json.loads((root/'data/refresh-status.json').read_text())['status'],'complete')
            self.assertFalse((root/'data/.daily-refresh.lock').exists())

    def test_failure_stops_and_unlocks(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with patch.object(daily,'ROOT',root),patch.object(daily.subprocess,'run',side_effect=RuntimeError('offline')) as run:
                with self.assertRaises(RuntimeError):daily.main()
            self.assertEqual(run.call_count,1)
            self.assertEqual(json.loads((root/'data/refresh-status.json').read_text())['status'],'failed')
            self.assertFalse((root/'data/.daily-refresh.lock').exists())

    def test_existing_lock_blocks_run(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'data').mkdir();lock=root/'data/.daily-refresh.lock';lock.write_text('123')
            with patch.object(daily,'ROOT',root),patch.object(daily.subprocess,'run') as run:
                with self.assertRaises(SystemExit):daily.main()
                run.assert_not_called()
            self.assertTrue(lock.exists())

if __name__=='__main__':unittest.main()
