#!/usr/bin/env python3
"""GOAL100 HONEST13/V2/V3 — canonical builder for the 13/14-engine champions (frozen 2026-09-02).

History: V2 (HONEST13V2_*) was first emitted by a coordinator heredoc that was NOT committed.
AUDIT_V2 flagged this as a PROVENANCE HOLE; this file is the remediation — the exact emission
code, frozen, with --verify reproducing the committed CSVs.

Construction (superset of honest11_build.py; identical 11-pool recipe, plus):
  - 2 (V2) or 3 (V3) new decorrelated sleeves at capital SLOT weight 0.10 vs 1.0 for each
    11-pool sleeve (slots 12.2 / 12.3): diescrack_L40Z20 (SR 1.01, corr 0.05, HUNT_BASIS2),
    CFX4 (SR 1.91, corr 0.00, HUNT_CARRYFX), [FF2_DUALGATE (SR 1.03, corr 0.14, HUNT_FF2)]
  - new sleeves are already net of their internal costs; they get the SAME per-sleeve vt
    (0.08, cap 8) so the gross accounting is uniform. Note: on federal holidays the 11 pool
    sleeves are absent (sn() calendar) while the new sleeves often print; rows-kept convention
    keeps those rows (new-sleeve PnL + costs only).
  - instrument-cost adjustment on the SLOT-WEIGHTED scale book (capW.diff()), exact
    position-path overlay turnover charged (full = capW * global * throttle),
    borrow 0.5%/yr (dualmom HTB uplift) on pool sleeves at slot weights.

Usage: python3 campaign/scripts/honest13_build.py [--verify] [--verify-v3] [--emit-v3]
"""
import sys; sys.path.insert(0, 'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT = "/Users/daxu/software/world-trader"

POOL = {
 "brwt15": "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "brwt10": "campaign/agents/COORD/sleeves/brwt10_2000.csv",
 "brwt7" : "campaign/agents/COORD/sleeves/brwt7.csv",
 "brwt5" : "campaign/agents/COORD/sleeves/brwt5.csv",
 "C5ng"  : "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "A5r2"  : "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "a6r7"  : "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
}
EXEC = {'brwt15':1.5,'brwt10':1.5,'brwt7':1.5,'brwt5':1.5,'C5ng':5,'C5ngsum':5,'A5r2':6,
        'a6r7':5,'QAxasts':8,'carryv2':8,'dualmom':15}
SHORTF = {'dualmom':0.5,'QAxasts':0.4,'carryv2':0.3,'C5ng':0.5,'C5ngsum':0.5,
          'brwt15':0.5,'brwt10':0.5,'brwt7':0.5,'brwt5':0.5,'A5r2':0,'a6r7':0}
NEW2 = {
 "diescrack": "campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
 "CFX4":      "campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
NEW3 = dict(NEW2)
NEW3["FF2"] = "campaign/agents/loop_team/HUNT_FF2/sleeves/FF2_DUALGATE_poolvt_daily.csv"

cal = USFederalHolidayCalendar(); hol = set(cal.holidays(start='2006-01-01', end='2026-12-31').date)
def sn(p):
    r = load(p).dropna()
    keep = np.array([(d.dayofweek < 5 and d.date() not in hol) for d in r.index])
    out = pd.Series(0.0, index=r.index[keep]); cu = 0.0; ki = 0; v = r.values
    for i in range(len(r)):
        cu += v[i]
        if keep[i]: out.iloc[ki] = cu; cu = 0.0; ki += 1
    return out.iloc[:ki]

def make(NEW, SW=0.10, PS=0.08):
    RAW = {}
    for n, p in POOL.items(): RAW[n] = sn(p)
    for n, p in NEW.items(): RAW[n] = load(p).dropna()
    names = list(RAW.keys())
    slots = {n: (1.0 if n in POOL else SW) for n in names}
    tot_slot = sum(slots.values())
    wts = pd.Series({n: slots[n]/tot_slot for n in names}, dtype=float)
    S = {}; V0 = {}
    for n, r in RAW.items():
        v, sv = vt(r, PS); S[n] = sv; V0[n] = v
    Sd = pd.DataFrame(S).dropna(how='all')
    capW = Sd.mul(wts, axis=1)
    V = {}
    for n in names:
        v = V0[n]
        if n in POOL:
            V[n] = v - capW[n].diff().abs().fillna(0) * ((EXEC[n]-6.0)/1e4)
        else:
            V[n] = v
    Vn = pd.DataFrame(V)
    W = Sd.div(Sd.sum(axis=1), axis=0).fillna(0)
    blend = (Vn.mul(wts, axis=1)).sum(axis=1)
    blend = blend[blend.index >= '2006-10-01']
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    return Sd, capW, blend, tw, wts

def build(Sd, capW, blend, tw, wts, TGT, THR):
    b, gb = vt(blend, TGT)
    eq = (1 + b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm - 1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc; dsc = sc.diff().abs()*0.5
    full = capW.mul(gb, axis=0).mul(sc, axis=0)
    reb = full.diff().abs().sum(axis=1)
    r_out = b - (tw.reindex(b.index).fillna(0) + dsc.fillna(0))*6e-4 - reb.reindex(b.index).fillna(0)*6e-4
    terms = []
    for n in POOL:
        sf = SHORTF[n]
        if sf > 0:
            terms.append(capW[n]*sc*sf*(0.005 + (0.03 if n == 'dualmom' else 0.0)*0.2))
    htb = pd.concat(terms, axis=1).sum(axis=1)
    return (r_out - htb.reindex(r_out.index).fillna(0)/252).dropna(how='all')

def family(tag, NEW):
    Sd, capW, blend, tw, wts = make(NEW)
    A = build(Sd, capW, blend, tw, wts, 0.07, 0.04)
    B = build(Sd, capW, blend, tw, wts, 0.091, 0.03)
    BAL = ((A+B)/2).dropna()
    return {
        f"GOAL100_{tag}_BALANCED_daily.csv": BAL,
        f"GOAL100_{tag}_SAFE_daily.csv": A,
        f"GOAL100_{tag}_AGGRESSIVE_daily.csv": B,
    }

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--verify'
    if mode == '--emit-v3':
        for fn, r in family("HONEST14V3", NEW3).items():
            r.to_frame('ret').to_csv(f"{ROOT}/campaign/results/{fn}")
            eq = (1+r).cumprod(); rr = r[r.index >= '2008-03-31']
            m = (1+rr).resample('ME').prod()-1
            yr = rr.groupby(rr.index.year).apply(lambda x: (1+x).prod()-1)
            print(f"wrote {fn} n={len(r)} ann08+ {( (1+rr).prod()**(252/len(rr))-1)*100:.1f}% "
                  f"SR_d {rr.mean()/rr.std()*np.sqrt(252):.2f} SR_m {m.mean()/m.std()*np.sqrt(12):.2f} "
                  f"MDD {((1+rr).cumprod()/(1+rr).cumprod().cummax()-1).min()*100:.2f}% "
                  f"neg08+ {(yr<0).sum()}/{yr.size}")
        return
    tag = "HONEST14V3" if mode == '--verify-v3' else "HONEST13V2"
    NEW = NEW3 if mode == '--verify-v3' else NEW2
    for fn, r in family(tag, NEW).items():
        path = f"{ROOT}/campaign/results/{fn}"
        try:
            old = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
        except FileNotFoundError:
            print(f"{fn}: NO COMMITTED FILE (run --emit-v3 first)"); continue
        j = pd.concat([old.rename('old'), r.rename('new')], axis=1, join='inner').dropna()
        md = float((j.old - j.new).abs().max())
        extra = "" if len(j) == max(len(old), len(r)) else f" (INDEX MISMATCH old={len(old)} new={len(r)})"
        print(f"{fn}: max|new-old|={md:.3e} {'IDENTICAL' if md < 1e-12 else 'DIFF'}{extra}")

if __name__ == "__main__":
    main()
