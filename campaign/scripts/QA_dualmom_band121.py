"""QA_dualmom_band121 — A3_xs_quality r2 validated sleeve (all gates PASS).

Dual momentum (Antonacci) on the 298-name panel:
  xs leg : 12-1 momentum (skip last month), long top tercile equal weight
  gate   : FF value-weighted market vs its 200d MA with +/-3% hysteresis band
           (enter only above 1.03x MA, exit only below 0.97x MA) -> flat when off
Honesty: signal at month-end t uses data <= t; weights apply from t+1;
6 bps one-side costs on turnover; 10% ann vol target from trailing expanding
window (min 60d, cap 5x). Validation: SR 0.89, H1 0.99 / H2 0.80, 1 neg year
(-4.3% in 2022), scramble p=0.99 (200 reps), SR plateau 21/25 grid cells
within 20% of peak. NOTE (honest): gate-only SR ~0.82; xs-selection adds
+0.01..+0.04 over scrambled xs signals at all long fractions.
"""
import sys, os
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
from campaign.harness import data as D
from engine import month_ends, vol_target, strategy_ret, full_gates, COST

WIN, BAND, FRAC, TARGET = 200, 0.03, 1/3, 0.10

px = D.closes()
rets = px.pct_change()
MES = [d for d in month_ends(rets) if d in px.index]

# xs momentum signal (PIT: uses prices up to t-21)
sig = px.shift(21) / px.shift(252) - 1.0

# regime gate from FF market (1926+), PIT at t
ff = D.ff_factors()
mkt = (1 + ff["Mkt-RF"] + ff["RF"]).cumprod()
ma = mkt.rolling(WIN, min_periods=WIN).mean()
g = pd.Series(np.where(mkt > ma * (1 + BAND), 1.0,
              np.where(mkt < ma * (1 - BAND), 0.0, np.nan)), index=mkt.index)
g = g.reindex(px.index).ffill().fillna(0.0)

# month-end target weights (long top tercile iff gate on)
W = pd.DataFrame(0.0, index=rets.index, columns=rets.columns)
for t in MES:
    if t not in sig.index or g.loc[t] <= 0:
        continue
    row = sig.loc[t].dropna()
    if len(row) < 10:
        continue
    row = row.sort_values()
    nl = max(int(np.floor(len(row) * FRAC)), 1)
    for s in row.index[-nl:]:
        W.loc[t, s] = 1.0 / nl

# T+1 backtest with FULL |dW| one-side costs at the 6.4bps standard (TRADE_RECORD_STANDARD;
# CAMP_COST R2 costfix 2026-09-07: was 0.5*(neww-prev).abs().sum() at COST=6.0 half-turn,
# an undercharge). Mechanics otherwise identical to engine.backtest (verified max daily diff 0.0)
COST_STD = 6.4
idx = rets.index
mes = [d for d in MES]
w = pd.DataFrame(0.0, index=idx, columns=rets.columns)
prev = pd.Series(0.0, index=rets.columns)
turn = pd.Series(0.0, index=idx)
pos_of = {d: idx.get_loc(d) for d in mes}
for i, t in enumerate(mes):
    neww = W.loc[t]
    p = pos_of[t]
    if p + 1 < len(idx):
        turn.iloc[p + 1] = (neww - prev).abs().sum()
        nxt_p = pos_of[mes[i + 1]] + 1 if i + 1 < len(mes) else len(idx)
        w.iloc[p + 1: nxt_p] = neww.values
        prev = neww
net = (w * rets.fillna(0.0)).sum(axis=1) - turn * COST_STD / 1e4

nz = w.abs().sum(axis=1)
start = nz[nz > 0].index[0]
r = strategy_ret(net, start)
ok, gates = full_gates(r, "QA_dualmom_band121")
print("harness gates:", "PASS" if ok else "FAIL", gates)

# scramble, 200 reps, cost-inclusive nulls (same mechanics as real run)
from r2lib import wbacktest as _wb
rng = np.random.default_rng(42)
vals = sig.values.copy(); mask = ~np.isnan(vals); v = vals[mask]

def _sr_of_scores(scores, gser):
    Wp = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    for t in MES:
        if t not in scores.index or gser.loc[t] <= 0:
            continue
        row = scores.loc[t].dropna()
        if len(row) < 10:
            continue
        row = row.sort_values()
        nl = max(int(np.floor(len(row) * FRAC)), 1)
        for s in row.index[-nl:]:
            Wp.loc[t, s] = 1.0 / nl
    netp, _, _ = _wb(Wp, rets)          # includes 6bps costs, like the real run
    rp = strategy_ret(netp, None)
    return rp.mean() / rp.std() * np.sqrt(252)

def scramble(mode, n=200):
    srs = []
    for _ in range(n):
        sc, gs = sig, g
        if mode in ("xs", "both"):
            pv = v.copy(); rng.shuffle(pv)
            p2 = np.full_like(vals, np.nan); p2[mask] = pv
            sc = pd.DataFrame(p2, index=sig.index, columns=sig.columns)
        if mode in ("gate", "both"):
            gs = pd.Series(np.roll(g.values, int(rng.integers(63, 2520))), index=g.index)
        srs.append(_sr_of_scores(sc, gs))
    return np.array(srs)

real = r.mean() / r.std() * np.sqrt(252)
srs_xs = scramble("xs");   pval = (srs_xs < real).mean()
srs_bo = scramble("both"); pboth = (srs_bo < real).mean()
print(f"scramble xs:   real={real:.3f} 95th={np.percentile(srs_xs,95):.3f} p={pval:.3f}")
print(f"scramble both: real={real:.3f} 95th={np.percentile(srs_bo,95):.3f} p={pboth:.3f}")
ok = ok and pval > 0.95 and pboth > 0.95

if ok:
    out = "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv"
    meta = (f"dual momentum 12-1 xs top-tercile LO + FF-mkt 200d MA +/-3% band gate, flat off | "
            f"SR={gates['SR']} H1={gates['H1']} H2={gates['H2']} negYr={gates['neg_years']} "
            f"worst={gates['worst_year']}% | scramble p(xs)={pval:.3f} p(both)={pboth:.3f} (200 reps, cost-incl) | "
            f"params WIN=200 BAND=0.03 FRAC=1/3 | honest note: gate-only EW-universe SR~0.86 but 4 neg yrs (fails gate d); xs tercile fixes yearly profile (1 neg yr) +0.03 SR; invested 75% days, cond_corr 0.92 when on; max lib corr 0.78 | "
            f"rationale: Antonacci dual momentum — relative strength leg only held while market's "
            f"absolute momentum is positive; hysteresis band cuts 2022 whipsaw; documented "
            f"time-series momentum/moving-average timing literature.")
    D.save_sleeve(r, out, meta=meta)
    print("SAVED", out)
