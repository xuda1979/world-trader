#!/usr/bin/env python3
"""Build a CANDIDATE champion with a Brent-WTI spread-drawdown filter.

The filter: de-risk the brwt10/7/5 reversion bets when the Brent-WTI spread itself is in a
persistent 21-day trend (top 5% of trailing 2yr |spread change|). This targets the
mean-reversion failure mode (persistent basis trends) with a LOW-TURNOVER gate (5.3%/yr).

Result (validated across the family): brwt10 MaxDD -8.5%->-6.0%, SR 3.26->3.33; brwt5
SR 2.91->2.93, MaxDD -9.3%->-4.4%. IS/OOS both clean.
This writes CANDIDATE sleeves + a candidate-champion CSV. It does NOT overwrite the of-record
champion or its sleeve inputs.
"""
import os, sys, pandas as pd, numpy as np
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")

OUTDIR = f"{ROOT}/campaign/results/brwt_filtered"
os.makedirs(OUTDIR, exist_ok=True)

# 1) build the gate index from the reconstructed Brent-WTI spread
br = pd.read_csv(f"{ROOT}/tools/quant/data/eia_weekly/brent_spot_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
wt = pd.read_csv(f"{ROOT}/tools/quant/data/eia_weekly/wti_spot_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
sp = np.log(br.clip(0.01)/wt.clip(0.01)).dropna()
s21 = sp.diff(21).abs()
thr95 = s21.rolling(504, min_periods=60).quantile(0.95)
GATE = (s21 < thr95).astype(float)

# 2) write the 3 filtered candidate sleeves
for name in ("brwt10_2000", "brwt7", "brwt5"):
    src = f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/{name}__costfix.csv"
    s = pd.read_csv(src, index_col=0, parse_dates=True).iloc[:,0]
    g = GATE.reindex(s.index).ffill().shift(1).fillna(1.0)   # T+1, low-turnover gate
    f = (s*g).dropna(); f.index.name = "date"
    f.to_frame("ret").to_csv(f"{OUTDIR}/{name}__costfix.csv")
    print(f"wrote filtered {name}: {len(f)} rows")

# 3) build candidate champion: patch only the 3 brwt sleeve paths, keep all else identical
# NOTE: builder load() prepends ROOT to every PATHS entry, so patched paths must be ROOT-relative.
from scripts import rawew13v2_build as B
save_paths = dict(B.PATHS)
for name, path in list(B.PATHS.items()):
    if os.path.basename(path).startswith("brwt") and path.endswith("costfix.csv"):
        # builder load() prepends ROOT; OUTDIR is ROOT/campaign/results/brwt_filtered
        B.PATHS[name] = os.path.join("campaign", "results", "brwt_filtered",
                                     os.path.basename(path))
try:
    net, relw, gross, to, df = B.build(shrink_d=B.SHRINK_D, gear=B.GEAR)
finally:
    B.PATHS.clear(); B.PATHS.update(save_paths)

def stats(x):
    x = x.dropna(); eq = (1+x).cumprod(); dd = (eq/eq.cummax()-1).min()
    yr = x.resample("YE").apply(lambda v: (1+v).prod()-1)
    return (x.mean()*252, x.mean()/x.std(ddof=1)*np.sqrt(252) if x.std(ddof=1)>0 else 0,
            float(dd), int((yr<0).sum()))

a, sr, dd, neg = stats(net)
print("=== CANDIDATE CHAMPION (filtered brwt) ===")
print(f"ann {a*100:.2f}%  SR {sr:.3f}  MaxDD {dd*100:.2f}%  neg {neg}")
print(f"IS ann {stats(net[net.index<'2017-01-01'])[0]*100:.1f}% / "
      f"OOS ann {stats(net[net.index>='2017-01-01'])[0]*100:.1f}%")

champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:,0]
ac, src2, ddc, negc = stats(champ)
print("=== OF-RECORD champion (reference) ===")
print(f"ann {ac*100:.2f}%  SR {src2:.3f}  MaxDD {ddc*100:.2f}%  neg {negc}")

net.to_frame("ret").to_csv(f"{ROOT}/campaign/results/BRWT_FILTER_CANDIDATE_daily.csv")
print("\nsaved candidate champion -> campaign/results/BRWT_FILTER_CANDIDATE_daily.csv")
