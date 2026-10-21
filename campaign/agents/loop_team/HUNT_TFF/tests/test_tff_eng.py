import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))), "campaign"))

def test_module():
    import tff_eng  # noqa

def test_z_no_lookahead():
    import pandas as pd, numpy as np, tff_eng
    s = pd.Series(np.random.RandomState(0).normal(0, 1, 200))
    z1 = tff_eng.z(s)
    s2 = s.copy(); s2.iloc[199] = 1e6
    z2 = tff_eng.z(s2)
    assert (z1.iloc[:150].fillna(0) == z2.iloc[:150].fillna(0)).all()

def test_fade_and_mom():
    import pandas as pd, tff_eng
    zs = pd.Series([2.0, -2.0, 0.0])
    assert list(tff_eng.fade(zs)) == [-1.0, 1.0, 0.0]
    assert list(tff_eng.mom_sig(zs)) == [1.0, -1.0, 0.0]

def test_live_daily_lag():
    import pandas as pd, tff_eng
    sig = pd.Series([1.0, 1.0], index=pd.DatetimeIndex(["2020-01-05", "2020-01-12"]))
    px_idx = pd.bdate_range("2020-01-06", periods=10)
    out = tff_eng.live_daily(sig, px_idx, lag_days=3)
    assert out.iloc[0] == 0.0          # 01-06 < 01-05+3d: no info yet
    assert out.iloc[-1] == 1.0

def test_diff_series():
    import tff_eng
    d = tff_eng.diff_series("sp500_emini", "asset_mgr", "dealer")
    assert len(d) > 500
