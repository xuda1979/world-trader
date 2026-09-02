#!/usr/bin/env python3
"""GOAL100 HONEST11 — canonical corrected champion builder (frozen 2026-09-02).

WHY THIS EXISTS: the committed STRICTTRADE champion included XGB1y, a MONTHLY-rebalance
book whose monthly PnL was FLATTENED into a constant daily return ("spread to daily").
That erased intra-month volatility, inflating measured daily SR 5.24 and understating the
honest risk path (see campaign/agents/LOOP_XGB1YFLAT/FINDINGS.md). HONEST11 removes that
defective sleeve, yielding the 11-sleeve pool below.

Honest stats (BALANCED, 2008-03-31..2026-07-31, n=4522):
  ann(geo) 47.9% | SR_daily 4.22 | SR_monthly 4.19 | MaxDD -4.85% | 0/19 neg years | OOS17+ 44.1%
  (SR_monthly is the honest single number — it removes intra-month autocorrelation artifacts
   equally across the 11 genuinely-daily sleeves; see STRICTAUDIT_SLEEVES verdict.)

Construction = recovered STRICTTRADE recipe EXACTLY, XGB1y excluded. Verified to reproduce
the committed GOAL100_HONEST11_daily_* files byte-for-byte (max|diff| < 1e-12).

Usage: python3 campaign/scripts/honest11_build.py [--verify]
"""
import sys; sys.path.insert(0, 'campaign/scripts')
import numpy as np, pandas as pd
from champion_build import load, vt
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)

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

cal = USFederalHolidayCalendar(); hol = set(cal.holidays(start='2006-01-01', end='2026-12-31').date)
def sn(p):
    r = load(p).dropna()
    keep = np.array([(d.dayofweek < 5 and d.date() not in hol) for d in r.index])
    out = pd.Series(0.0, index=r.index[keep]); cu = 0.0; ki = 0; v = r.values
    for i in range(len(r)):
        cu += v[i]
        if keep[i]: out.iloc[ki] = cu; cu = 0.0; ki += 1
    return out.iloc[:ki]

N = len(POOL); Sn = pd.DataFrame({n: vt(sn(p), 0.10)[1] for n, p in POOL.items()}).dropna(how='all')
capW = Sn / N

def build(TGT, THR, PERSLEEVE=0.10, REBAL=False, KEEP=False):
    """PERSLEEVE=0.10 + REBAL=False + KEEP=False -> committed HONEST11 (byte-exact).
    PERSLEEVE=0.08 -> committed HONEST11L16 (byte-exact).
    KEEP=True: calendar rows-kept fix (blend keeps rows where ANY sleeve trades; borrow
    charged only on sleeves present) — clears the L16_AUDIT inner-join finding.
    REBAL=True: charge 6bps/side on the vol-target-overlay rebalance turnover
    (sum_i |d scale_i|/N + |d global scalar|) — clears the uncharged-cost finding."""
    V = {}; S = {}
    # weights/scale book from the SAME per-sleeve target as returns (audit-recovered
    # L16 recipe: vt target applied to BOTH return scaling AND the Sn scale book
    # (cap weights, turnover, borrow) — see VET_HONESTY FINDINGS §1 provenance)
    SnP = pd.DataFrame({n: vt(sn(p), PERSLEEVE)[1] for n, p in POOL.items()}).dropna(how='all')
    capWP = SnP / N
    for n in POOL:
        r = sn(POOL[n])
        v, s = vt(r, PERSLEEVE)
        V[n] = v - capWP[n].diff().abs().fillna(0) * ((EXEC[n]-6.0)/1e4)
        S[n] = s
    Vn = pd.DataFrame(V); Sd = pd.DataFrame(S)
    W = SnP.div(SnP.sum(axis=1), axis=0).fillna(0)
    blend = Vn.mean(axis=1); blend = blend[blend.index >= '2006-10-01']
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    b = vt(blend, TGT)[0]
    eq = (1 + b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm - 1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc; dsc = sc.diff().abs()*0.5
    r_out = b - (tw.reindex(b.index).fillna(0) + dsc.fillna(0)) * 6e-4
    if REBAL:
        # vol-target overlay rebalance: per-sleeve scale turnover + global scalar turnover,
        # both on the full scaled notional; one-side, 6bps.
        reb = Sd.diff().abs().sum(axis=1)/N + vt(blend, TGT)[1].diff().abs().fillna(0)
        r_out = r_out - reb.reindex(r_out.index).fillna(0) * 6e-4
    htb = pd.Series(0.0, index=Sn.index)
    terms = []
    for n in POOL:
        sf = SHORTF[n]
        if sf > 0:
            gn = SnP[n]/N * sc * sf
            terms.append(gn*(0.005 + (0.03 if n == 'dualmom' else 0.0)*0.2))
    if KEEP:
        # rows-kept fix (L16_AUDIT calendar finding): keep every blend row; borrow
        # charged ONLY on sleeves actually present that day (skipna sum).
        htb = pd.concat(terms, axis=1).sum(axis=1) if terms else pd.Series(0.0, index=r_out.index)
        r_out = r_out - htb.reindex(r_out.index).fillna(0)/252
        return r_out.dropna(how='all')
    # committed semantics: NaN in ANY borrow term propagates -> row dropped (inner join)
    for gn in terms:
        htb = htb + gn
    return (r_out - htb/252).dropna()

def emit(tag, A, B):
    BAL = ((A+B)/2).dropna()
    outs = {
        f"GOAL100_{tag}_BALANCED_daily.csv": BAL,
        f"GOAL100_{tag}_SAFE_daily.csv": A,
        f"GOAL100_{tag}_AGGRESSIVE_daily.csv": B,
    }
    return outs

def main(verify):
    A = build(0.07, 0.04); B = build(0.091, 0.03); BAL = ((A+B)/2).dropna()
    mode = sys.argv[1] if len(sys.argv) > 1 else ('--verify' if verify else '')
    if mode == '--verify-l16':
        # HONEST11L16: per-sleeve vt 0.08 (audit-recovered recipe), committed files
        outs = emit("HONEST11L16", build(0.07, 0.04, 0.08), build(0.091, 0.03, 0.08))
        for fn, r in outs.items():
            old = pd.read_csv(f"{ROOT}/campaign/results/{fn}", index_col=0, parse_dates=True).iloc[:, 0]
            j = pd.concat([old.rename('old'), r.rename('new')], axis=1, join='inner').dropna()
            md = float((j.old - j.new).abs().max())
            print(f"{fn}: max|new-old|={md:.3e} {'IDENTICAL' if md < 1e-12 else 'DIFF'}")
        return
    if mode == '--fixed':
        # CORRECTED champion: calendar rows-kept + vt-rebalance costs charged
        outs = emit("HONEST11FIX", build(0.07, 0.04, 0.08, REBAL=True, KEEP=True),
                    build(0.091, 0.03, 0.08, REBAL=True, KEEP=True))
        for fn, r in outs.items():
            path = f"{ROOT}/campaign/results/{fn}"
            r.to_frame('ret').to_csv(path)
            eq = (1+r).cumprod(); mdd = (eq/eq.cummax()-1).min()*100
            m = (1+r).resample('ME').prod()-1
            srm = m.mean()/m.std()*np.sqrt(12); srd = r.mean()/r.std()*np.sqrt(252)
            ann = (1+r).prod()**(252/len(r))-1
            yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
            print(f"wrote {fn} n={len(r)} ann {ann*100:.1f}% SR_d {srd:.2f} SR_m {srm:.2f} "
                  f"MDD {mdd:.2f}% neg {(yr<0).sum()}/{yr.size} worst {yr.min()*100:.1f}%")
        return
    outs = {
        "GOAL100_HONEST11_daily_BALANCED_daily.csv": BAL,
        "GOAL100_HONEST11_daily_SAFE_daily.csv": A,
        "GOAL100_HONEST11_daily_AGGRESSIVE_daily.csv": B,
    }
    for fn, r in outs.items():
        path = f"{ROOT}/campaign/results/{fn}"
        old = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
        j = pd.concat([old.rename('old'), r.rename('new')], axis=1, join='inner').dropna()
        md = float((j.old - j.new).abs().max())
        eq = (1+r).cumprod(); mdd = (eq/eq.cummax()-1).min()*100
        m = (1+r).resample('ME').prod()-1; srm = m.mean()/m.std()*np.sqrt(12)
        srd = r.mean()/r.std()*np.sqrt(252); ann = (1+r).prod()**(252/len(r))-1
        if verify:
            print(f"{fn}: max|new-old|={md:.3e} {'IDENTICAL' if md < 1e-12 else 'DIFF'}  "
                  f"(ann {ann*100:.1f}% SR_d {srd:.2f} SR_m {srm:.2f} MDD {mdd:.2f}%)")
        else:
            r.to_frame('ret').to_csv(path)
            print(f"wrote {fn} n={len(r)} ann {ann*100:.1f}% SR_m {srm:.2f}")

if __name__ == "__main__":
    main(any(m in sys.argv for m in ('--verify',)))
