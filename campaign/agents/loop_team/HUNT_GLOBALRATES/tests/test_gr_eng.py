import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))), "campaign"))

def test_module():
    import gr_eng  # noqa

def test_panel_loads():
    import gr_eng
    p = gr_eng.panel()
    assert p.shape[1] >= 6 and len(p) > 500

def test_synchrony_signal_range():
    import gr_eng
    p = gr_eng.panel()
    sig = gr_eng.synchrony_signal(p)
    assert sig.dropna().between(0, 1).all()
    assert sig.index[0] > p.index[0]    # lag applied

def test_us_lead_confirm():
    import numpy as np, gr_eng
    p = gr_eng.panel()
    sig = gr_eng.us_lead_signal(p)
    v = sig.dropna()
    assert v.isin([-1.0, 0.0, 1.0]).all()
