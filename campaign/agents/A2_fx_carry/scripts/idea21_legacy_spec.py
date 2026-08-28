"""Idea 21: legacy COT spec (noncomm) positioning on commodities 1986-2016, FRED prices.
Both directions (fade/follow), z-score + change variants, weekly."""
import sys; sys.path.insert(0, "campaign/scripts"); sys.path.insert(0, "campaign/harness")
from a2_lib import cot_weekly, px_series, daily_align
from util import cost, vol_target, gates, halves_ok, yearly, scramble_test
import pandas as pd, numpy as np

nets = cot_weekly("legacy", "spec")

def asset_leg(net_w, asset, mode, lb, thr):
    z = (net_w - net_w.rolling(lb).mean()) / net_w.rolling(lb).std()
    z = z.clip(-2, 2)
    if mode == "fade":
        sig = np.sign(-z).where(z.abs() >= thr, 0.0)
    else:  # follow
        sig = np.sign(z).where(z.abs() >= thr, 0.0)
    px = px_series(asset)
    pos = sig.reindex(sig.index.union(px.index)).ffill().shift(1).reindex(px.index).ffill().fillna(0)
    gross = (pos * px.pct_change().shift(-1)).dropna()
    return vol_target(cost(gross, pos.diff().abs().fillna(0)), 0.10)

sr = lambda x: x.mean()/x.std()*np.sqrt(252) if x.std()>0 else 0
for mode in ("fade", "follow"):
    for lb in (52, 104, 156):
        for thr in (1.0, 1.5):
            legs = {}
            for a, net in nets.items():
                legs[a] = asset_leg(net, a, mode, lb, thr)
            df = pd.DataFrame(legs).fillna(0)
            start = df.apply(lambda c: c.ne(0).idxmax()).max()
            combo = vol_target(df.loc[df.index >= start].mean(axis=1), 0.10).dropna()
            g = gates(combo); h1, h2 = halves_ok(combo)
            print(f"legacy {mode} lb={lb} thr={thr}: SR={g.get('sr',0):.2f} H1={h1:.2f} H2={h2:.2f} n={len(combo)} pass={g.get('pass_')} [{g.get('why','')}]")
# per-asset best variant diagnostics
print("-- per-asset fade lb=104 thr=1.0 --")
for a, net in nets.items():
    r = asset_leg(net, a, "fade", 104, 1.0)
    r = r[r.index >= r.ne(0).idxmax()]
    print(f"  {a:6s} SR={sr(r):5.2f} n={len(r)} {r.index[0].date()}..{r.index[-1].date()}")
