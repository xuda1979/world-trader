import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../.."))
def test_module():
    import macro_eng  # noqa
def test_longflat():
    import pandas as pd, numpy as np, macro_eng
    s = pd.Series(np.r_[np.zeros(400) + 1.0, np.full(30, 5.0)],
                  index=pd.bdate_range("2020-01-01", periods=430))
    lf = macro_eng.longflat(s, win=252, minp=126)
    assert lf.iloc[-1] == 1.0
def test_zsig_invert():
    import pandas as pd, numpy as np, macro_eng
    s = pd.Series(np.r_[np.zeros(400), np.full(30, 4.0)],
                  index=pd.bdate_range("2020-01-01", periods=430))
    assert macro_eng.zsig(s).iloc[-1] == 1.0
    assert macro_eng.zsig(s, invert=True).iloc[-1] == -1.0
def test_mom_gate():
    import pandas as pd, macro_eng
    s = pd.Series([100.0] * 100 + [110.0] * 20,
                  index=pd.bdate_range("2020-01-01", periods=120))
    g = macro_eng.mom_gate(s, lb=21)
    assert g.iloc[-1] == 1.0
