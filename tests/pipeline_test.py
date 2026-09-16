"""Tests for the actual numerical and persistence failure modes."""
import datetime as dt
import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pipeline'))
from analyze import derive,percentile
from eda import risk_score
from update import aggregate,export_forecast,promote

class PipelineTests(unittest.TestCase):
    def test_midrank_ties_and_full_archive(self):
        values=pd.Series([0.0]*30+[100.0]);months=pd.Series([1]*31)
        rank,threshold=percentile(values,months)
        self.assertAlmostEqual(rank.iloc[0],100*15/31)
        self.assertEqual(threshold['1']['n'],31)
        self.assertGreater(rank.iloc[-1],95)
        self.assertLess(rank.iloc[-1],100)
    def test_minimum_reference(self):
        rank,_=percentile(pd.Series([1.0]*29),pd.Series([1]*29))
        self.assertTrue(rank.isna().all())
    def test_rolling_and_current_period_used(self):
        dates=pd.date_range('2025-01-01','2026-02-01')
        frame=pd.DataFrame({'date':dates,'rain':1.0,'q':10.0,'tmax':30.0,'wind':5.0})
        derived,base=derive(frame)
        self.assertEqual(base['q']['1']['n'],62)
        self.assertTrue(pd.isna(derived.r3.iloc[1]))
        self.assertEqual(derived.r7.iloc[6],7)
        self.assertTrue((derived.loc[derived.date.dt.month==1,'severity']==0).all())
    def test_score_weights(self):
        full=risk_score(pd.Series(dict(qp=90,rp=50,tp=20,wp=80)))
        self.assertEqual(full['score'],76)
        fallback=risk_score(pd.Series(dict(qp=None,rp=50,tp=20,wp=80)),False)
        self.assertEqual(fallback['score'],62)
        self.assertIsNone(risk_score(pd.Series(dict(qp=None,rp=None,tp=None,wp=None)))['score'])
    def test_forecast_preserves_provider_timestamps(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);daily={'time':['2026-09-16'],'precipitation_sum':[1]}
            obj={'retrieved_at':'2026-09-16T12:00:00Z','weather':{'x':{'daily':daily}},'flood':{'x':{'daily':{'time':['2026-09-16'],'river_discharge_median':[2],'river_discharge_p25':[1],'river_discharge_p75':[3]}}},'weather_at':{'x':'2026-09-16T12:00:00Z'},'flood_at':{'x':'2026-09-14T12:00:00Z'}}
            (root/'current.json').write_text(json.dumps(obj));export_forecast(root)
            data=pd.read_csv(root/'forecast-daily.csv');self.assertEqual(data.flood_retrieved_utc.iloc[0],obj['flood_at']['x'])
    def test_complete_hourly_day(self):
        units=dict(precipitation='mm',temperature_2m='°C',relative_humidity_2m='%',wind_speed_10m='km/h',pressure_msl='hPa')
        hourly={'time':pd.date_range('2026-01-01',periods=24,freq='h').astype(str).tolist(),**{k:[v]*24 for k,v in [('precipitation',1),('temperature_2m',30),('relative_humidity_2m',80),('wind_speed_10m',10),('pressure_msl',1000)]}}
        data=aggregate({'hourly':hourly,'hourly_units':units},'ERA5');self.assertEqual(data.rain.iloc[0],24)
        hourly['precipitation'][0]=None
        self.assertTrue(pd.isna(aggregate({'hourly':hourly,'hourly_units':units},'ERA5').rain.iloc[0]))
    def test_release_promotion(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);destination=root/'data';stage=root/'staged';destination.mkdir();stage.mkdir()
            (destination/'value').write_text('old');(stage/'value').write_text('new')
            promote(stage,destination);self.assertEqual((destination/'value').read_text(),'new');self.assertFalse((root/'data.previous').exists())
if __name__=='__main__':unittest.main()
