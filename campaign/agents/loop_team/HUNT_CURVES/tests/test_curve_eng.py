import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../.."))

def test_module():
    import curve_eng  # noqa

def test_slope_spread():
    import pandas as pd, curve_eng
    df = pd.DataFrame({"2Y": [1.0, 1.0], "10Y": [2.0, 3.0]})
    out = curve_eng.slope_spread(df)
    assert list(out) == [1.0, 2.0]

def test_zscore_no_lookahead():
    import pandas as pd, numpy as np, curve_eng
    s = pd.Series(np.random.RandomState(0).normal(0, 1, 500))
    z1 = curve_eng.zscore(s, win=100, minp=50)
    s2 = s.copy(); s2.iloc[499] = 1e6
    z2 = curve_eng.zscore(s2, win=100, minp=50)
    assert (z1.iloc[:400].fillna(0) == z2.iloc[:400].fillna(0)).all()

def test_signal_modes():
    import pandas as pd, curve_eng
    z = pd.Series([2.0, -2.0])
    assert list(curve_eng.curve_signal(z, mode="mom")) == [1.0, -1.0]
    assert list(curve_eng.curve_signal(z, mode="rev")) == [-1.0, 1.0]

def test_engine_smoke():
    import pandas as pd, numpy as np, curve_eng
    idx = pd.bdate_range("2015-01-01", periods=800)
    px = pd.Series(np.cumprod(1 + np.random.RandomState(1).normal(0.0002, 0.01, 800)), index=idx)
    feat = pd.Series(np.random.RandomState(2).normal(0, 1, 800).cumsum(), index=idx)
    net = curve_eng.run_curve_sleeve(feat, px)
    assert len(net) > 500 and net.abs().max() < 0.2
