#!/usr/bin/env python3
"""HUNT_CRYPTO2 ROUND 4 audit — independent re-derivations of other agents' DEAD_IDEAS rows.

Runs the cited scripts' MATH with my own code (not their FINDINGS prose) to catch
shared-bug masking. Full-gauntlet reproductions are the cited scripts themselves,
executed byte-unchanged (sha256s in script_sha_before.txt / script_sha_after.txt);
their outputs are in audit*_*.txt next to this file.
"""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/scripts")


def sleeve_stats(r):
    r = r.dropna()
    sr = r.mean() / r.std() * np.sqrt(252)
    h = len(r) // 2
    h1 = r.iloc[:h].mean() / r.iloc[:h].std() * np.sqrt(252)
    h2 = r.iloc[h:].mean() / r.iloc[h:].std() * np.sqrt(252)
    yr = (1 + r).resample('YE').prod() - 1
    ann = (1 + r).prod() ** (252 / len(r)) - 1
    return (f"n={len(r)} {r.index[0].date()}->{r.index[-1].date()} SR={sr:.3f} "
            f"ann={ann * 100:.1f}% H1={h1:+.2f} H2={h2:+.2f} negyr={int((yr < 0).sum())} "
            f"worst={yr.min() * 100:.1f}%")


# ---- row 100 CMDT2-R3: saved sleeves re-measured (no shared code) ----
print("== row 100 CMDT3 saved sleeves ==")
for nm in ["CMDT3_Sprd_DBE_DBP_LS_63d", "CMDT3_Sprd_DBE_DBP_LO_63d",
           "CMDT3_Sprd_USCI_DBC_LO_126d", "CMDT3_Sprd_USCI_DBC_LS_21d"]:
    r = pd.read_csv(f"{ROOT}/campaign/agents/chief/coord/HUNT_CMDT2/sleeves/{nm}.csv",
                    index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    print(f"  {nm}: {sleeve_stats(r)}")

# ---- row 102 CREDIT2-R3: spread momentum re-derived WITHOUT their script ----
print("== row 102 CREDIT2 spread momentum, own-code re-derivation (no VT/borrow) ==")
COST = 6.4 / 1e4
for hi, lo in [("HYG", "LQD"), ("JNK", "IEF")]:
    A, B = (pd.read_csv(f"{ROOT}/tools/quant/data/more_etf/{s}.csv", index_col=0,
                        parse_dates=True)['close'].astype(float).sort_index() for s in (hi, lo))
    R = pd.concat({'A': A.pct_change(), 'B': B.pct_change()}, axis=1, sort=True).dropna()
    sig = np.sign(np.log(A / B).reindex(R.index).diff(63))
    W = pd.DataFrame({'A': sig, 'B': -sig}, index=R.index).fillna(0.0)
    We = W.shift(1).fillna(0.0)
    net = (We * R).sum(axis=1) - We.diff().abs().sum(axis=1).fillna(0.0) * COST
    print(f"  {hi}/{lo}: {sleeve_stats(net)}")

# ---- row 103 CREDIT2-R3: static carry harvest re-derivation ----
print("== row 103 static carry harvest (HYG TR-proxy minus IEF TR-proxy) ==")
from HUNT_CREDIT2_round3 import px, yld, total_return  # noqa: E402  (their data plumbing)


def tr(sym, sid):
    return total_return(px(sym), yld(sid))


Rc = pd.concat({'HIY': tr("HYG", "BAA10Y"), 'IG': tr("IEF", "DGS10")},
               axis=1, sort=True).dropna()
Rd = (Rc['HIY'] - Rc['IG']).dropna()
arith = Rd.mean() * 252
geo = (1 + Rd).prod() ** (252 / len(Rd)) - 1
print(f"  raw 1:1 differential: arith={arith * 100:+.2f}%/yr geo={geo * 100:+.2f}%/yr "
      f"n={len(Rd)}  (row claims -1.90%/yr pre-cost = arithmetic)")
W = pd.DataFrame({'HIY': 1.0, 'IG': -1.0}, index=Rc.index)
net, We, g = __import__('HUNT_CREDIT2_round3').net_of(W, Rc)
print(f"  sleeve: {sleeve_stats(net)}  (row claims netSR -0.30, gross -0.26 w/ VT, "
      f"H -0.47/-0.08, 10 negyr worst -24.6%, corr -0.123)")

# ---- row 98 COT_ITER11: same-period vs forward corr artifact per their docstring ----
print("== row 98 corr(COT weekly delta, market weekly return) same vs forward ==")
PRICES = {'gold': ('tools/quant/data/twelvedata/GLD.csv', 'close'),
          'silver': ('tools/quant/data/more_etf/SLV.csv', None),
          'copper': ('tools/quant/hedge_fund_strats/data_fred/copx.csv', None),
          'corn': ('tools/quant/data/more_etf/CORN.csv', None),
          'soybeans': ('tools/quant/data/more_etf/SOYB.csv', None),
          'natgas': ('tools/quant/data/more_etf/UNG.csv', None),
          'wti': ('tools/quant/data/more_etf/USO.csv', None),
          'sugar': ('tools/quant/data/more_etf/CANE.csv', None),
          'wheat': ('tools/quant/data/more_etf/WEAT.csv', None)}
COT = {'gold': 'gold_cot.csv', 'silver': 'silver_cot.csv', 'copper': 'copper_cot.csv',
       'corn': 'corn_cot.csv', 'soybeans': 'soybeans_cot.csv',
       'natgas': 'nat_gas_nymex_cot.csv', 'wti': 'crude_wti_nymex_cot.csv',
       'sugar': 'sugar_no11_cot.csv', 'wheat': 'wheat_srw_cot.csv'}
for m, (p, col) in PRICES.items():
    cot = pd.read_csv(f"{ROOT}/tools/quant/data/more_cot/{COT[m]}", parse_dates=['date'])
    cot = cot.set_index('date')['net_noncomm_pct_oi'].astype(float).sort_index()
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0, parse_dates=True)
    pxs = (df[col] if col in df.columns else df.iloc[:, 0]).astype(float).dropna()
    j = pd.concat({"d": cot.resample('W-FRI').last().diff(1),
                   "r": pxs.resample('W-FRI').last().pct_change()},
                  axis=1, join="inner").dropna()
    print(f"  {m:9s} same={j.d.corr(j.r):+.3f} fwd={j.d.corr(j.r.shift(-1)):+.3f} n={len(j)}")

# ---- champion of record spot-check ----
ch = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                 index_col=0, parse_dates=True).iloc[:, 0].astype(float)
nav = (1 + ch).cumprod()
mdd = ((nav - nav.cummax()) / nav.cummax()).min()
yr = (1 + ch).resample('YE').prod() - 1
ann = (1 + ch).prod() ** (252 / len(ch)) - 1
print(f"== champion: ann={ann * 100:.3f}% SR={ch.mean() / ch.std() * np.sqrt(252):.3f} "
      f"MDD={mdd * 100:.2f}% negyr={int((yr < 0).sum())} "
      f"(of record: 37.195 / 3.181 / -6.69 / 0) ==")
