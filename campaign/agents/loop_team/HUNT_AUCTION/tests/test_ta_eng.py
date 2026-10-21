import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../.."))
def test_module():
    import ta_eng  # noqa
def test_daily_btc_ffill():
    import pandas as pd, ta_eng
    df = pd.DataFrame({"auction_date": pd.to_datetime(["2020-01-02", "2020-01-09"]),
                       "type": ["Bill", "Bill"], "bid_to_cover": [2.5, 3.0]})
    s = ta_eng.daily_btc(df)
    assert len(s) == (pd.Timestamp("2020-01-09") - pd.Timestamp("2020-01-02")).days + 1
    assert s.iloc[1] == 2.5 and s.iloc[-1] == 3.0
def test_indirect_share():
    import pandas as pd, ta_eng
    df = pd.DataFrame({"auction_date": pd.to_datetime(["2020-01-05"]), "type": ["Note"],
                       "indirect_accepted_mmn": [20.0], "competitive_accepted_mmn": [40.0]})
    s = ta_eng.indirect_share(df)
    assert abs(s.iloc[-1] - 0.5) < 1e-9
def test_zgate_sign():
    import pandas as pd, numpy as np, ta_eng
    s = pd.Series(np.r_[np.zeros(300), np.full(30, 5.0)],
                  index=pd.bdate_range("2020-01-01", periods=330))
    g = ta_eng.zgate(s)
    assert g.iloc[-1] == 1.0
def test_run_on_equity_smoke():
    import pandas as pd, numpy as np, ta_eng
    from bt import backtest as btb
    idx = pd.bdate_range("2015-01-01", periods=800)
    px = pd.Series(np.cumprod(1 + np.random.RandomState(0).normal(0.0003, 0.01, 800)), index=idx)
    r = px.pct_change()
    net = btb.sleeve(pd.Series(1.0, index=idx), r.to_frame("a"))
    assert len(net) > 500
