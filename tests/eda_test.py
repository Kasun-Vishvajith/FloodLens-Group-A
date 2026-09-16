"""Unit checks for the transparent district risk-score calculation."""
import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('eda', ROOT / 'pipeline' / 'eda.py')
eda = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eda)


def test_full_score():
    row = pd.Series({'qp': 90, 'rp': 50, 'tp': 20, 'wp': 80})
    result = eda.risk_score(row)
    assert result['score'] == 76.0
    assert result['basis'] == 'flood 50% + rainfall 30% + weather 20%'


def test_missing_components_rescale():
    row = pd.Series({'qp': None, 'rp': 50, 'tp': 20, 'wp': 80})
    result = eda.risk_score(row, has_flow=False)
    assert result['score'] == 62.0
    assert 'available weights rescaled' in result['basis']


def test_no_components_is_unavailable():
    result = eda.risk_score(pd.Series({'qp': None, 'rp': None, 'tp': None, 'wp': None}))
    assert result['score'] is None
    assert result['basis'] == 'Unavailable'


if __name__ == '__main__':
    test_full_score()
    test_missing_components_rescale()
    test_no_components_is_unavailable()
    print('PASS: risk-score weights, fallbacks and unavailable handling')
