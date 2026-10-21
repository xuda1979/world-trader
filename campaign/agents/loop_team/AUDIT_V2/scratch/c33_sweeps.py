#!/usr/bin/env python3
"""AUDIT_V2 check 7: T+1 probe (extra-lag on new sleeves), flatten gate, block-boot SR CI,
leave-one-out of the 13 sleeves (drop each; check neg yrs + stats swing) — on my reconstruction."""
import numpy as np, pandas as pd, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import POOL as POOL11, NEW, EXEC, SHORTF, load, vt

def sn_raw(p):
    r = load(p).dropna()
    return r[r.index.dayofweek < 5]

def build(TGT, THR, SLOT=0.10, extra_lag=(), drop=None, PS=0.08):
    ALL = dict(POOL11, **NEW)
    POOLS = [n for n in POOL11 if n not in (drop or {})]
    NEWS = [n for n in NEW if n not in (drop or {})]
    R13 = {}
    for n in POOLS:
        r = sn_raw(POOL11[n])
        if n in extra_lag: r = r.shift(1)
        R13[n] = r
    for n in NEWS:
        r = sn_raw(NEW[n])
        if n in extra_lag: r = r.shift(1)
        R13[n] = r
    idx = pd.concat(R13.values(), axis=1).dropna(how='all').index
    wv = pd.Series({**{n: 1.0 for n in POOLS}, **{n: SLOT for n in NEWS}})
    NSUM = wv.sum()
    Sd = pd.DataFrame({n: vt(R13[n], PS)[1].reindex(idx) for n in R13})
    capWP = pd.DataFrame({n: vt(R13[n], PS)[1] for n in POOLS}).dropna(how='all')/11
    V = {}
    for n in POOLS:
        v, s = vt(R13[n], PS)
        V[n] = v.reindex(idx) - capWP[n].diff().abs().reindex(idx).fillna(0)*((EXEC[n]-6.0)/1e4)
    for n in NEWS:
        V[n] = vt(R13[n], PS)[0].reindex(idx)
    Vn = pd.DataFrame(V)
    blend = (Vn*wv).sum(axis=1)/NSUM
    blend = blend[blend.index >= '2006-10-01']
    b, gs = vt(blend, TGT)
    eq = (1+b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm-1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc
    dsc = sc.diff().abs()*0.5
    r = b - dsc.fillna(0)*6e-4
    reb = (Sd.mul(wv, axis=1)).diff().abs().sum(axis=1)/NSUM + gs.diff().abs().fillna(0)
    r = r - reb.reindex(r.index).fillna(0)*6e-4
    terms = [Sd[n].reindex(r.index).fillna(0)/11*sc*SHORTF[n]*(0.005+(0.03 if n=='dualmom' else 0)*0.2)
             for n in POOLS if SHORTF[n]>0 and n in Sd.columns]
    htb = pd.concat(terms, axis=1).sum(axis=1, skipna=True)
    r = r - htb/252
    return r.dropna(how='all')

def stats(r):
    r = r.dropna()
    srd = r.mean()/r.std()*np.sqrt(252)
    m = (1+r).resample('ME').prod()-1
    srm = m.mean()/m.std()*np.sqrt(12)
    eq = (1+r).cumprod(); mdd = (eq/eq.cummax()-1).min()
    ann = eq.iloc[-1]**(252/len(r))-1
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    return srd, srm, mdd*100, ann*100, int((yr<0).sum()), yr.size

# baseline
A = build(0.07, 0.04); B = build(0.091, 0.03); BAL = ((A+B)/2).dropna()
srd, srm, mdd, ann, neg, ny = stats(BAL)
print(f"baseline recon BAL: ann {ann:.2f}% SR_d {srd:.3f} SR_m {srm:.3f} MDD {mdd:.2f}% neg {neg}/{ny}")

# T+1 extra-lag probe on new sleeves
A = build(0.07, 0.04, extra_lag=NEW.keys()); B = build(0.091, 0.03, extra_lag=NEW.keys())
BAL = ((A+B)/2).dropna()
srd, srm, mdd, ann, neg, ny = stats(BAL)
print(f"T+1 extra-lag on NEW: ann {ann:.2f}% SR_d {srd:.3f} SR_m {srm:.3f} MDD {mdd:.2f}% neg {neg}/{ny}")

# T+1 extra-lag on ALL 13 (execution-timing artifact test)
A = build(0.07, 0.04, extra_lag=set(POOL11)|set(NEW)); B = build(0.091, 0.03, extra_lag=set(POOL11)|set(NEW))
BAL = ((A+B)/2).dropna()
srd, srm, mdd, ann, neg, ny = stats(BAL)
print(f"T+1 extra-lag on ALL: ann {ann:.2f}% SR_d {srd:.3f} SR_m {srm:.3f} MDD {mdd:.2f}% neg {neg}/{ny}")

# flatten gate on committed V2 BAL
v2 = pd.read_csv("/Users/daxu/software/world-trader/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2s = pd.read_csv("/Users/daxu/software/world-trader/campaign/results/GOAL100_HONEST13V2_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2a = pd.read_csv("/Users/daxu/software/world-trader/campaign/results/GOAL100_HONEST13V2_AGGRESSIVE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
ac1 = v2.autocorr(1); uniq = v2.nunique()/len(v2)
# zero-runs
vals = v2.values; runs = []; cur = 1
for i in range(1, len(vals)):
    if vals[i] == 0.0 and vals[i-1] == 0.0: cur += 1
    else:
        if cur > 1: runs.append(cur)
        cur = 1
if cur > 1: runs.append(cur)
print(f"flatten: ac1 {ac1:.4f} uniqR {uniq:.4f} exact-zero rows {int((v2==0).sum())} max zero-run {max(runs) if runs else 0}")
srd, srm, mdd, ann, neg, ny = stats(v2)
print(f"committed BAL stats: ann {ann:.2f}% SR_d {srd:.3f} SR_m {srm:.3f} MDD {mdd:.2f}% neg {neg}/{ny}")

# block-bootstrap SR CI (2000x, 10-day blocks) on committed BAL, 2008+
r08 = v2[(v2.index >= '2008-03-31') & (v2.index <= '2026-07-31')]
def boot(r, B=2000, blk=10, seed=11):
    x = r.dropna().values; n = len(x); nb = n//blk
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, n-blk, size=(B, nb))
    srs = np.empty(B)
    for i, row in enumerate(starts):
        xb = np.concatenate([x[s:s+blk] for s in row])[:n]
        srs[i] = xb.mean()/xb.std()*np.sqrt(252)
    return srs
srs = boot(r08)
print(f"block-boot SR (2008+, 2000x): mean {srs.mean():.3f} p5 {np.percentile(srs,5):.3f} p95 {np.percentile(srs,95):.3f} p(SR<=0) {float((srs<=0).mean()):.4f}")
srsf = boot(v2)
print(f"block-boot SR (full span):    mean {srsf.mean():.3f} p5 {np.percentile(srsf,5):.3f} p95 {np.percentile(srsf,95):.3f} p(SR<=0) {float((srsf<=0).mean()):.4f}")

# leave-one-out of the 13
print("\nLOYO (drop one sleeve at a time, BAL recon):")
for dn in sorted(set(POOL11) | set(NEW)):
    A = build(0.07, 0.04, drop={dn}); B = build(0.091, 0.03, drop={dn})
    BAL = ((A+B)/2).dropna()
    srd, srm, mdd, ann, neg, ny = stats(BAL)
    flag = " <-- NEG YR" if neg > 0 else ""
    print(f"  -{dn:10s}: ann {ann:6.2f}% SR_d {srd:.3f} SR_m {srm:.3f} MDD {mdd:6.2f}% neg {neg}/{ny}{flag}")
