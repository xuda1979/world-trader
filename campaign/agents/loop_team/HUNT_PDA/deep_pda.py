"""Deep-gate soma_share_lf_hi_QQQ (0.534-0.536, 4-6 neg): compare vs B&H (long-flat on SPY
with 50%+ exposure is mostly drift). Blend test vs champion too."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "campaign"))
import numpy as np, pandas as pd
import pda_eng
from bt import gates
from bt.engine import lag_signal, vol_target_scale, cap_leverage, cost_turnover, borrow_cost, margin_cost

df = pda_eng.load_a()
base = pda_eng.share_daily(df, "soma_accepted_mmn")
sig = (base > base.rolling(252, min_periods=126).median()).astype(float)
sig.index = base.index   # already lagged inside share_daily

for sym in ("QQQ", "SPY"):
    d = pd.read_csv(os.path.join(ROOT, "tools/quant/data/twelvedata", f"{sym}.csv"), parse_dates=["date"])
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
    p, real = gates.scramble_positions(wc["w"], r)
    bh = r.reindex(net.index).dropna()
    bh_sr = float(bh.mean() / bh.std() * np.sqrt(252))
    print(f"{sym}: SR={rep['sr']:.3f} neg={rep['neg_years']} scr_p={p:.3f} exposure={float((wc['w']>0).mean()):.2f} B&H_SR={bh_sr:.2f}")

# champion blend
champ = pd.read_csv(os.path.join(ROOT, "campaign/results/GOAL100_HONEST_RAWEW13_GEAR16_daily.csv"), parse_dates=[0])
c = champ.set_index(champ.columns[0]).iloc[:, 0].astype(float)
d = pd.read_csv(os.path.join(ROOT, "tools/quant/data/twelvedata", "QQQ.csv"), parse_dates=["date"])
px = d.set_index("date")["close"].astype(float).sort_index()
r = px.pct_change()
sig_a = sig.reindex(r.index).ffill().fillna(0.0)
scale = vol_target_scale(r).fillna(1.0)
w = (lag_signal(sig_a) * scale).fillna(0.0)
wc = cap_leverage(w.to_frame("w"), max_lev=1.6)
net = (wc["w"] * r - cost_turnover(wc, 6.4) - borrow_cost(wc, 0.005)
       - margin_cost(wc["w"].abs(), 0.045, 1.6)).dropna()
j = pd.concat([c.rename("c"), net.rename("g")], axis=1, join="inner").dropna()
sr0 = float(j["c"].mean() / j["c"].std() * np.sqrt(252))
for wgt in (0.05, 0.10, 0.20, 0.30):
    bl = (1 - wgt) * j["c"] + wgt * j["g"]
    sr = float(bl.mean() / bl.std() * np.sqrt(252))
    print(f"blend w={wgt}: dSR={sr - sr0:+.3f}")
