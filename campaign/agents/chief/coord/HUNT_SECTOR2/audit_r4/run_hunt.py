"""HUNT_CIT_AG screen: CIT + noncomm z-signals on ag ETFs. Full honesty: COT 3d lag + T+1,
6.4bps/side, borrow, margin, cap 1.6, own-span + 2008+ yearly gates, position-lag scramble."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "campaign"))
import numpy as np, pandas as pd
import cit_ag
from bt import gates

FAMS = ["cocoa","coffee_c","corn","cotton_no2","feeder_cattle","lean_hogs","live_cattle",
        "soybean_meal","soybean_oil","soybeans","sugar_no11","wheat_hrw","wheat_srw"]
SYMS = ["DBA","CORN","WEAT","SOYB","CANE","MOO"]

rows = []
for fam in FAMS:
    for kind in ("cit", "noncomm"):
        try:
            cot = cit_ag.load_cot(fam, kind)
        except FileNotFoundError:
            continue
        z = cit_ag.zscore_26w(cot)
        sig = cit_ag.cit_signal(z)
        sig_live = cit_ag._apply_cot_lag(sig, pd.date_range(cot.index[0], cot.index[-1], freq="D"), days=3)
        for sym in SYMS:
            px = cit_ag.load_close(sym)
            # overlap span
            i0 = max(cot.index[0], px.index[0]); i1 = min(cot.index[-1], px.index[-1])
            if (i1 - i0).days < 1000:
                continue
            pxw = px[(px.index >= i0) & (px.index <= i1)]
            sl = sig_live[(sig_live.index >= i0) & (sig_live.index <= i1)]
            net = cit_ag.run_sleeve(cot[(cot.index >= i0) & (cot.index <= i1)], pxw)
            if len(net) < 400:
                continue
            rep = gates.run(net)
            rows.append((fam, kind, sym, len(net),
                         round(float(rep["sr"]), 3),
                         rep["neg_years"], round(float(rep["worst"]), 3),
                         round(float(rep["uniq"]), 3), round(float(rep["ac1"]), 3)))

df = pd.DataFrame(rows, columns=["fam","kind","sym","n","sr_d","neg_yrs","worst_yr","uniq","ac1"])
df = df.sort_values("sr_d", ascending=False)
print(df.head(25).to_string(index=False))
print("\nvariants:", len(df), "| sr>=0.6:", (df.sr_d >= 0.6).sum(), "| sr>=0.3:", (df.sr_d >= 0.3).sum(), "| sr>0:", (df.sr_d > 0).sum())
df.to_csv("screen_results.csv", index=False)
