"""Deep-gate the top variant: lean_hogs noncomm -> SOYB. Cross-pair sanity + scramble + spans."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "campaign"))
import numpy as np, pandas as pd
import cit_ag
from bt import gates

cot = cit_ag.load_cot("lean_hogs", "noncomm")
px = cit_ag.load_close("SOYB")
net = cit_ag.run_sleeve(cot, px)
print("full span:", len(net), net.index[0].date(), "->", net.index[-1].date())
rep = gates.run(net)
print({k: (round(float(v), 3) if isinstance(v, (int, float, np.floating)) else v)
       for k, v in rep.items() if not k.endswith("_ok") and k not in ("pass",)})

# yearly
yr = net.groupby(net.index.year).apply(lambda x: (1 + x).prod() - 1)
print("yearly:", {int(k): round(float(v), 3) for k, v in yr.items()})

# scramble (position-lag) on the real book
z = cit_ag.zscore_26w(cot)
sig = cit_ag.cit_signal(z)
sig_live = cit_ag._apply_cot_lag(sig, pd.date_range(cot.index[0], cot.index[-1], freq="D"), days=3)
r = px.pct_change().to_frame("a")
from bt.engine import lag_signal, vol_target_scale
scale = vol_target_scale(r.iloc[:, 0]).fillna(1.0)
w = (lag_signal(sig_live.reindex(r.index).fillna(0)) * scale).fillna(0).to_frame("w")
from bt.engine import cap_leverage
wc = cap_leverage(w, max_lev=1.6)
p, real_sr = gates.scramble_positions(wc["w"], r.iloc[:, 0])
print("scramble p:", round(p, 4), "(real SR baseline:", round(real_sr, 3), ")")

# cross-tradable robustness (same signal, different instrument = same underlying complex?)
for sym in ("CORN", "DBA", "WEAT", "CANE", "MOO"):
    px2 = cit_ag.load_close(sym)
    net2 = cit_ag.run_sleeve(cot, px2)
    if len(net2) > 400:
        r2 = gates.run(net2)
        print(f"xcheck {sym}: SR={r2['sr']:.3f} neg={r2['neg_years']}")

# cross-family: lean_hogs signal on own proxy absent; check signal-corr across tradables
print("\n== parameter neighborhood (lean_hogs noncomm -> SOYB) ==")
for entry, exit_z in ((1.0, 0.5), (1.5, 0.5), (2.0, 0.5), (1.5, 0.0), (1.5, 1.0), (2.0, 1.0)):
    net3 = cit_ag.run_sleeve(cot, px, entry=entry, exit_z=exit_z)
    r3 = gates.run(net3)
    print(f"entry={entry} exit={exit_z}: SR={r3['sr']:.3f} neg={r3['neg_years']} H2={r3['h2']:.3f}")
