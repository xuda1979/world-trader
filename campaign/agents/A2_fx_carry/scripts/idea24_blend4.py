"""Idea 24: equal-weight blend of r2's best independent candidates (campaign thesis:
many low-corr sleeves blended). Components designed separately, equal weights, no tuning:
A rates LF (2y+10y 378d), B TSMOM L/S 252d ex-bonds, C gold complex (MR+trend), D TFF AM-mom 52w."""
import sys; sys.path.insert(0, "campaign/agents/A2_fx_carry/scripts")
sys.path.insert(0, "campaign/scripts"); sys.path.insert(0, "campaign/harness")
from a2_lib import px_series, cot_weekly, weekly_pos_from_change, asset_sleeve
from idea16_fred_breadth import tsmom_asset
from idea19_gold_ratio import mr_leg, gold_trend
from util import cost, vol_target, gates, halves_ok, yearly, scramble_test
import pandas as pd, numpy as np

# A: rates long/flat
def rates_lf():
    legs = []
    for nm in ("UST2","UST10"):
        px = px_series(nm)
        pos = (px/px.shift(378) - 1 > 0).astype(float).fillna(0)
        gross = (pos*px.pct_change().shift(-1)).dropna()
        legs.append(vol_target(cost(gross, pos.diff().abs().fillna(0)), 0.10))
    return pd.concat(legs, axis=1).mean(axis=1)

# B: cross-asset TSMOM long/short (no bonds)
def tsmom_exb():
    assets = ["SPY","QQQ","XAU","SLV","WTI","BRENT","NATGAS","COPX","EUR","JPY","GBP","CAD","DXY"]
    legs = pd.DataFrame({a: tsmom_asset(a, 252) for a in assets})
    return legs.mean(axis=1)

# C: gold complex
def gold_complex():
    return vol_target(pd.DataFrame({"mr": mr_leg(252, 2.0, 0.5), "gt": gold_trend(126)}).mean(axis=1), 0.10).dropna()

# D: TFF AM-mom 52w
def am_mom():
    nets = cot_weekly("tff", "am")
    book = {a: asset_sleeve(weekly_pos_from_change(net, 52, 0.0), a) for a, net in nets.items()}
    df = pd.DataFrame(book).fillna(0)
    start = df.apply(lambda c: c.ne(0).idxmax()).max()
    return vol_target(df.loc[df.index >= start].mean(axis=1), 0.10).dropna()

A, B, C, D = rates_lf(), tsmom_exb(), gold_complex(), am_mom()
comps = {"A_ratesLF": A, "B_tsmom_exb": B, "C_gold": C, "D_amom": D}
for k, v in comps.items():
    g = gates(v.dropna()); h1, h2 = halves_ok(v.dropna())
    print(f"{k:12s} SR={g.get('sr',0):.2f} H1={h1:.2f} H2={h2:.2f} n={len(v.dropna())} pass={g.get('pass_')} [{g.get('why','')}]")
dfc = pd.DataFrame(comps).dropna(how="all").fillna(0.0)
corr = dfc.corr()
print("pairwise corr:\n", corr.round(2))
combo = vol_target(dfc.mean(axis=1), 0.10).dropna()
combo = combo[combo.index >= "2012-12-01"]  # all components live
g = gates(combo); h1, h2 = halves_ok(combo); yr = yearly(combo)
print(f"\nBLEND4: SR={g.get('sr',0):.2f} H1={h1:.2f} H2={h2:.2f} negyr={int((yr<0).sum())}/{len(yr)} worst={yr.min()*100:.1f}% n={len(combo)} {combo.index[0].date()}..{combo.index[-1].date()} pass={g.get('pass_')} [{g.get('why','')}]")
print("yearly:", {int(k): round(v*100,1) for k,v in yr.items()})
