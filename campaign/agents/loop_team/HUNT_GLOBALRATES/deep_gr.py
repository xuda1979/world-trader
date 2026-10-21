"""Deep-gate sync126 longflat QQQ (0.584, 1 neg): the signature looks like the NFCIRISK gate —
low-exposure longflat drift. Check exposure, B&H comparison, scramble, blend dSR vs champion."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "campaign"))
import numpy as np, pandas as pd
import gr_eng
from bt import gates
from bt.engine import lag_signal, vol_target_scale, cap_leverage, cost_turnover, borrow_cost, margin_cost

p = gr_eng.panel()
sig = gr_eng.synchrony_signal(p, lb=126, up_q=0.5)
sig.index = sig.index   # already lagged

champ = pd.read_csv(os.path.join(ROOT, "campaign/results/GOAL100_HONEST_RAWEW13_GEAR16_daily.csv"), parse_dates=[0])
c = champ.set_index(champ.columns[0]).iloc[:, 0].astype(float)

d = pd.read_csv(os.path.join(ROOT, "tools/quant/data/twelvedata", "QQQ.csv"), parse_dates=["date"])
px = d.set_index("date")["close"].astype(float)
px = px[~px.index.duplicated(keep="last")].sort_index()
r = px.pct_change()
sig_a = sig.reindex(r.index).ffill().fillna(0.0)
scale = vol_target_scale(r).fillna(1.0)
w = (lag_signal(sig_a) * scale).fillna(0.0)
wc = cap_leverage(w.to_frame("w"), max_lev=1.6)
net = (wc["w"] * r - cost_turnover(wc, 6.4) - borrow_cost(wc, 0.005)
       - margin_cost(wc["w"].abs(), 0.045, 1.6)).dropna()
rep = gates.run(net)
p_sc, real = gates.scramble_positions(wc["w"], r)
bh = r.reindex(net.index).dropna()
print(f"SR={rep['sr']:.3f} neg={rep['neg_years']} worst={rep['worst']:.3f} scr_p={p_sc:.3f} "
      f"exposure={float((wc['w']>0).mean()):.2f} B&H={float(bh.mean()/bh.std()*np.sqrt(252)):.2f}")
yr = net.groupby(net.index.year).apply(lambda x: (1 + x).prod() - 1)
print("yearly:", {int(k): round(float(v), 3) for k, v in yr.items()})

j = pd.concat([c.rename("c"), net.rename("g")], axis=1, join="inner").dropna()
sr0 = float(j["c"].mean() / j["c"].std() * np.sqrt(252))
corr = float(j["c"].corr(j["g"]))
print("corr to champ:", round(corr, 3))
for wgt in (0.05, 0.10, 0.20, 0.30):
    bl = (1 - wgt) * j["c"] + wgt * j["g"]
    sr = float(bl.mean() / bl.std() * np.sqrt(252))
    print(f"blend w={wgt}: dSR={sr - sr0:+.3f}")
