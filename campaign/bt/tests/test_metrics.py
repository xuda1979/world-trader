"""TDD tests for bt.metrics."""
import numpy as np, pandas as pd
from bt import metrics as M


def test_sharpe_of_constant_is_zero():
    r = pd.Series(0.001, index=pd.date_range('2020-01-01', periods=10, freq='B'))
    assert M.sharpe_d(r) == 0.0


def test_ann_geo_matches_manual():
    r = pd.Series([0.01, -0.01, 0.02], index=pd.date_range('2020-01-01', periods=3, freq='B'))
    manual = (1.01 * 0.99 * 1.02) ** (252 / 3) - 1
    assert np.isclose(M.ann_geo(r), manual)


def test_max_dd():
    r = pd.Series([0.1, -0.5, 0.3, 0.4], index=pd.date_range('2020-01-01', periods=4, freq='B'))
    # peak 1.1, trough 0.55 -> dd = 0.55/1.1 - 1 = -0.5
    assert np.isclose(M.max_dd(r), 0.55 / 1.1 - 1, atol=1e-9)


def test_neg_years():
    # 2020: three returns; 2021: three returns; 2020 total negative, 2021 positive
    idx = pd.to_datetime(['2020-01-01', '2020-02-01', '2020-03-01',
                          '2021-01-01', '2021-02-01', '2021-03-01'])
    r = pd.Series([0.10, -0.05, -0.10, 0.10, 0.05, 0.08], index=idx)
    neg, worst = M.neg_years(r)
    assert neg == 1
    # worst = (1.10*0.95*0.90 - 1) = -0.0595
    assert np.isclose(worst, 1.10 * 0.95 * 0.90 - 1, atol=1e-9)


def test_half_split_not_nan():
    r = pd.Series(np.linspace(0.001, 0.002, 100),
                  index=pd.date_range('2020-01-01', periods=100, freq='B'))
    h1, h2 = M.half_split(r)
    assert h1 == h1 and h2 == h2  # NaN-safe (not NaN)
