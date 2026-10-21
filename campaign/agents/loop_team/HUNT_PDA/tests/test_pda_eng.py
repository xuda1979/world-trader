import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))), "campaign"))

def test_module():
    import pda_eng  # noqa

def test_share_daily_lag():
    import pandas as pd, pda_eng
    df = pd.DataFrame({"auction_date": pd.to_datetime(["2020-01-02"]),
                       "type": ["Note"], "total_accepted_mmn": [100.0],
                       "primary_dealer_accepted_mmn": [40.0]})
    s = pda_eng.share_daily(df, "primary_dealer_accepted_mmn")
    assert abs(s.iloc[0] - 0.4) < 1e-9
    # lag applied: value at 01-03 (1 day later)
    assert s.index[0] == pd.Timestamp("2020-01-03")

def test_z_window():
    import pandas as pd, numpy as np, pda_eng
    s = pd.Series(np.random.RandomState(0).normal(0.5, 0.1, 400))
    z1 = pda_eng.z(s)
    s2 = s.copy(); s2.iloc[399] = 1e6
    z2 = pda_eng.z(s2)
    assert (z1.iloc[:350].fillna(0) == z2.iloc[:350].fillna(0)).all()
