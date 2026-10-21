"""Global-rates screen: synchrony + US-lead gates on SPY/QQQ/EFA."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "campaign"))
import numpy as np, pandas as pd
import gr_eng
from bt import gates

p = gr_eng.panel()
print("panel:", p.shape, p.index[0].date(), "->", p.index[-1].date())
rows = []
def add(tag, net):
    if net is None or len(net) < 400: return
    rep = gates.run(net)
    rows.append((tag, len(net), round(float(rep["sr"]), 3), rep["neg_years"], round(float(rep["worst"]), 3)))

for lb in (21, 63, 126, 252):
    for up_q in (0.5, 0.6, 0.75):
        sig = gr_eng.synchrony_signal(p, lb=lb, up_q=up_q)
        for sym in ("SPY", "QQQ", "EFA"):
            try:
                add(f"sync{lb}_q{up_q}_{sym}", gr_eng.run(sig, sym))
            except FileNotFoundError:
                pass
    # US lead
    for confirm in (True, False):
        sig = gr_eng.us_lead_signal(p, lb=lb, confirm=confirm)
        for sym in ("SPY", "QQQ"):
            try:
                add(f"uslead{lb}{'_conf' if confirm else ''}_{sym}", gr_eng.run(sig, sym))
            except Exception:
                pass

d = pd.DataFrame(rows, columns=["tag","n","sr","neg","worst"]).sort_values("sr", ascending=False)
print(d.head(18).to_string(index=False))
print("variants:", len(d), "| sr>=0.3:", (d.sr >= 0.3).sum(), "| sr>0:", (d.sr > 0).sum())
d.to_csv("screen_gr.csv", index=False)
