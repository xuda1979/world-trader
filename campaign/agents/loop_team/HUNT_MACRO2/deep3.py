"""Deep-gate top macro gates: NFCIRISK_medinv_QQQ (0.952, 0 neg!). CRITICAL: check lookahead —
NFCI is published weekly (Fri ~15:00 for week ending Saturday). medinv uses level>rolling median.
Weekly series ffilled daily: information lag must be >= 4 days (Sat -> Wed conservative).
Rebuild with publish-lag then verify all gates + scramble."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "campaign"))
import numpy as np, pandas as pd
import macro_eng
from bt import gates
from bt.engine import lag_signal, vol_target_scale, cap_leverage, cost_turnover, borrow_cost, margin_cost

def build_book(sig, sym, pub_lag_days):
    """REAL book: signal available at date t must come from release <= t - pub_lag.
    Then positions = T+1 (bt lag) of the tradeable signal."""
    s = sig.copy()
    s.index = s.index + pd.Timedelta(days=pub_lag_days)   # release availability
    px = macro_eng.load_px(sym)
    r = px.pct_change()
    daily = s.reindex(pd.date_range(r.index[0], r.index[-1], freq="D")).ffill().reindex(r.index).ffill().fillna(0.0)
    scale = vol_target_scale(r).fillna(1.0)
    w = (lag_signal(daily) * scale).fillna(0.0)
    wc = cap_leverage(w.to_frame("w"), max_lev=1.6)
    net = (wc["w"] * r - cost_turnover(wc, 6.4) - borrow_cost(wc, 0.005)
           - margin_cost(wc["w"].abs(), 0.045, 1.6)).dropna()
    return net, wc["w"], r

s = macro_eng.load("NFCIRISK")
lf = 1.0 - macro_eng.longflat(s, 252, 126)   # risk-high => flat (medinv)
for lag in (0, 4, 6, 8):
    net, w, r = build_book(lf, "QQQ", lag)
    rep = gates.run(net)
    p, real = gates.scramble_positions(w, r)
    print(f"lag={lag}: SR={rep['sr']:.3f} neg={rep['neg_years']} worst={rep['worst']:.3f} scr_p={p:.3f}")

# also JTSJOL (monthly, BLS first Friday -> lag 5) and RRPONTSYD (daily, published ~16:15 same day -> lag 1)
for sid, lags in (("JTSJOL", (0, 5, 20)), ("RRPONTSYD", (0, 1, 3)), ("TEDRATE", (0, 1, 3))):
    try:
        s = macro_eng.load(sid)
    except FileNotFoundError:
        continue
    if sid == "JTSJOL":
        sig = macro_eng.longflat(s, 252, 126)
    else:
        sig = 1.0 - macro_eng.longflat(s, 252, 126)
    for lag in lags:
        net, w, r = build_book(sig, "QQQ", lag)
        rep = gates.run(net)
        print(f"{sid} lag={lag}: SR={rep['sr']:.3f} neg={rep['neg_years']} worst={rep['worst']:.3f}")
