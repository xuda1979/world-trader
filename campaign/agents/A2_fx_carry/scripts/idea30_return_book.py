"""Charter r4 final candidate: A2 RETURN book at vt15 = EW of
(a) rates long/flat 378d (UST2+UST10), (b) XAU lf126 trend, (c) CU lf3m trend.
Params chosen as family peaks from prior rounds a priori; plateau checked by +-1 notch sweep.
All gates incl. scramble on PRE-vt net returns (r2 lesson #5), corr<=0.3 to champion."""
import sys; sys.path.insert(0, __file__.rsplit("/",1)[0])
from r4_lib import *
from a2_lib import px_series
from idea26_metals_carry import trend_pos, copper_trend

def rates_lf(lb=378, vt=0.15, names=("UST2","UST10")):
    legs = []
    for nm in names:
        px = px_series(nm)
        pos = (px/px.shift(lb) - 1 > 0).astype(float).fillna(0)
        net, netvt = run_mech(pos, px, vt)
        legs.append(netvt)
    return pd.concat(legs, axis=1).mean(axis=1).dropna()

def gold_lf(lb=126, vt=0.15):
    px = px_fred("xau")
    return run_mech(trend_pos(px, lb, "lf"), px, vt)[1]

def cu_lf(lb=3, vt=0.15):
    return copper_trend(lb, "lf", vt)

if __name__ == "__main__":
    comps = {"rates": rates_lf(), "xau": gold_lf(), "cu": cu_lf()}
    for k, v in comps.items():
        g = full_gates(v); c, n = corr_to_champ(v)
        pr(f"  comp:{k}", g, c, f"n={n}")
    df = pd.DataFrame(comps).dropna(how="all").fillna(0.0)
    start = df.ne(0).any(axis=1).idxmax()
    blend_vt = vol_target(df.mean(axis=1), 0.15).dropna()
    blend = blend_vt[blend_vt.index >= start]
    g = full_gates(blend); c, n = corr_to_champ(blend)
    yr = yearly(blend)
    pr("A2-RETURN-blend-vt15", g, c, f"n={n}")
    print("  yearly:", {int(k): round(v*100,1) for k,v in yr.items()})
    # NOTE: yearly gate already failed (11 neg yrs, worst -14.7%); scramble moot.
