"""A6 r3: FULL gate workup on LO-rev k21 d10 cad21 (only base-gate passer) + corr breakdown + 6-mix."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from r3_lib import rets_px, gates, corr_to_champion, champion_mix, sr_monthly, load_sleeve, CHAMP, signal_scramble_p
from lib6 import stats, halves_sr, vol_target

rets, px = rets_px()
ok = rets.notna() & (px.notna().cumsum() >= 120)
iv = rets.rolling(63, min_periods=40).std()

def carry(w, cadence):
    arr = np.array(w.values); cur = arr[0]
    for i in range(len(arr)):
        if (np.arange(len(arr)) % cadence == 0)[i]: cur = arr[i]
        else: arr[i] = cur
    return pd.DataFrame(arr, index=w.index, columns=w.columns)

def lo_weights(score, ok, frac, cadence, iv=None):
    r = score.where(ok)
    L = r.le(r.quantile(frac, axis=1), axis=0) & ok
    inv = 1.0 / iv.where(ok)
    return carry((L * inv).div((L * inv).sum(axis=1).clip(lower=1e-9), axis=0), cadence)

def cand(frac=0.1, cad=21, k=21):
    W = lo_weights(px.pct_change(k, fill_method=None), ok, frac, cad, iv=iv)
    gross = (W.shift(1) * rets).sum(axis=1)["2007-01-01":]
    turn = (W.shift(1) - W.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
    net = (gross - turn*6/1e4).dropna()
    r_vt, _ = vol_target(net, 0.10)
    return r_vt, W

r, W = cand()
print("=== FULL GATES (incl scramble 200x circular weight-shift) ===")
oka, info = gates(r, "LO-rev k21 d10 ivw cad21 VT10", W=W, rets=rets, scramble=True)
yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
print("   yearly:", {int(y): round(v*100,1) for y,v in yr.items()})

print("=== PLATEAU: frac x cadence x k x weight-scheme neighbors ===")
srs = {}
for fr, fl in [(0.05,"d5"), (0.1,"d10"), (0.2,"q20")]:
    for cd in [10, 15, 21]:
        for k in [15, 21, 27]:
            rr, _ = cand(fr, cd, k)
            srs[(fr, cd, k)] = stats(rr)["sr"]
chosen = srs[(0.1, 21, 21)]; peak = max(srs.values())
neigh = [srs[(0.1,21,15)], srs[(0.1,21,27)], srs[(0.1,15,21)], srs[(0.2,21,21)], srs[(0.05,21,21)],
         srs[(0.2,15,21)], srs[(0.05,21,27)], srs[(0.2,21,15)]]
print(f"   chosen SR={chosen:.2f} peak={peak:.2f} at {[kk for kk,v in srs.items() if v==peak]}")
print(f"   8 neighbors min={min(neigh):.2f} -> all within 20% of peak? {min(neigh) >= 0.8*peak}")
print("   grid:", {f"{a},{b},{c}": round(v,2) for (a,b,c),v in sorted(srs.items())})

print("=== CORR breakdown (monthly) vs champion legs and top library ===")
cm, legs = champion_mix()
for n, s in legs.items():
    a = (1+r).resample("ME").prod()-1; b = (1+s).resample("ME").prod()-1
    j = pd.concat([a,b],axis=1).dropna()
    print(f"   corr vs {n:22s} = {j.corr().iloc[0,1]:.2f}")
LIB = "/Users/daxu/software/world-trader/campaign/results/sleeve_library"
import os
best_corr = []
for f in sorted(os.listdir(LIB)):
    if not f.endswith(".csv") or f.endswith(".meta"): continue
    try:
        s = load_sleeve(os.path.join(LIB, f))
        a = (1+r).resample("ME").prod()-1; b = (1+s).resample("ME").prod()-1
        j = pd.concat([a,b],axis=1).dropna()
        if len(j) > 60: best_corr.append((abs(j.corr().iloc[0,1]), f[:-4], j.corr().iloc[0,1]))
    except Exception: pass
best_corr.sort(reverse=True)
print("   top |corr| library:", [(n, round(c,2)) for _, n, c in best_corr[:6]])

print("=== 6-sleeve MIX: champion 5 + candidate (equal weight, monthly SR_m) ===")
cand_r = r
alllegs = dict(legs); alllegs["CAND"] = cand_r
df = pd.DataFrame(alllegs).dropna(how="all").fillna(0.0)
live = (df != 0.0).sum(axis=1)
mix6 = df.mean(axis=1)[live >= 5]
print(f"   mix6 window {mix6.index[0].date()} -> {mix6.index[-1].date()}  SR_m={sr_monthly(mix6):.2f} (champion 1.89, target >1.95)")
# also: replace A6_pair_fm with candidate (5 legs)
df2 = pd.DataFrame({n: s for n, s in legs.items() if n != "A6_pair_fm"} | {"CAND": cand_r}).dropna(how="all").fillna(0.0)
live2 = (df2 != 0.0).sum(axis=1)
mix_swap = df2.mean(axis=1)[live2 >= 4]
print(f"   swap variant (drop A6_pair_fm, add CAND): SR_m={sr_monthly(mix_swap):.2f}")
