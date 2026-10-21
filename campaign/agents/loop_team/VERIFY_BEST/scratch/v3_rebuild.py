"""VERIFY_BEST Object 1: INDEPENDENT rebuild of GOAL100_HONEST14V3 (V3 champion) from raw
sleeve files. My own code (does NOT import honest13_build); campaign/bt used for metrics +
capital accounting. Recipe re-derived from the frozen documented construction:
  11 pool sleeves (holiday-folded) + 3 new (0.10 slot vs 1.0) at slot/11.3 weights,
  per-sleeve vt(0.08, rolling60 shift1, cap8), exec-cost adj on slot book, global vt
  (SAFE 0.07/THR .04, AGGR 0.091/.03), throttle at trailing-126d-peak DD, costs 6.0bps/side
  on slot-weighted scale-book turnover + blend turnover + throttle, borrow 0.5%/yr (+HTB
  dualmom 0.6%/yr), BAL=(SAFE+AGGR)/2.
"""
import sys; sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
import numpy as np, pandas as pd
from bt import metrics as M
from pandas.tseries.holiday import USFederalHolidayCalendar
ROOT = "/Users/daxu/software/world-trader"

def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

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
NEW3 = {
 "diescrack": "campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
 "CFX4":      "campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
 "FF2":       "campaign/agents/loop_team/HUNT_FF2/sleeves/FF2_DUALGATE_poolvt_daily.csv",
}
hol = set(USFederalHolidayCalendar().holidays(start='2006-01-01', end='2026-12-31').date)

def sn(p):  # holiday folding: a holiday row's return rolls into the next kept (weekday) row
    r = load(p).dropna()
    keep = np.array([(d.dayofweek < 5 and d.date() not in hol) for d in r.index])
    out = pd.Series(0.0, index=r.index[keep]); cu = 0.0; ki = 0
    for i, v in enumerate(r.values):
        cu += v
        if keep[i]: out.iloc[ki] = cu; cu = 0.0; ki += 1
    return out

def vt(r, tgt, min_win=60, cap=8.0):
    vol = r.rolling(min_win).std().shift(1) * np.sqrt(252)   # trailing only
    s = (tgt / vol).clip(upper=cap); s[vol.isna()] = 0
    return r * s.fillna(0), s

# ---- per-sleeve stage
RAW, S, V0 = {}, {}, {}
for n, p in POOL.items(): RAW[n] = sn(p)
for n, p in NEW3.items(): RAW[n] = load(p).dropna()
names = list(RAW.keys())
slots = {n: (1.0 if n in POOL else 0.10) for n in names}
wts = pd.Series({n: slots[n]/sum(slots.values()) for n in names}, dtype=float)
for n in names:
    v, sv = vt(RAW[n], 0.08); S[n] = sv; V0[n] = v
Sd = pd.DataFrame(S).dropna(how='all')
capW = Sd.mul(wts, axis=1)
V = {}
for n in names:
    V[n] = V0[n] - capW[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4) if n in POOL else V0[n]
Vn = pd.DataFrame(V)
W = Sd.div(Sd.sum(axis=1), axis=0).fillna(0)          # turnover-accounting weights
blend = Vn.mul(wts, axis=1).sum(axis=1)
blend = blend[blend.index >= '2006-10-01']
tw = ((W - W.shift(1)).abs()*0.5).sum(axis=1)

def build(TGT, THR, leak_variant=None):
    b, gb = vt(blend, TGT)
    eq = (1+b.fillna(0)).cumprod()
    if leak_variant == 'sameday':
        rm = eq.rolling(126).max(); tdd = eq/rm - 1     # SAME-DAY (leaky) variant
    else:
        rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm - 1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index)
    b = b*sc; dsc = sc.diff().abs()*0.5
    full = capW.mul(gb, axis=0).mul(sc, axis=0)
    reb = full.diff().abs().sum(axis=1)
    r_out = b - (tw.reindex(b.index).fillna(0) + dsc.fillna(0))*6e-4 - reb.reindex(b.index).fillna(0)*6e-4
    terms = [capW[n]*sc*SHORTF[n]*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2)
             for n in POOL if SHORTF[n] > 0]
    htb = pd.concat(terms, axis=1).sum(axis=1)
    return (r_out - htb.reindex(r_out.index).fillna(0)/252).dropna(how='all'), gb, sc, full

SAFE, *_ = build(0.07, 0.04); AGGR, gb_a, sc_a, full_a = build(0.091, 0.03)
BAL = ((SAFE+AGGR)/2).dropna()

out = {}
for tag, mine in [('SAFE', SAFE), ('AGGRESSIVE', AGGR), ('BALANCED', BAL)]:
    old = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST14V3_{tag}_daily.csv",
                      index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([old.rename('old'), mine.rename('new')], axis=1, join='inner').dropna()
    md = float((j.old-j.new).abs().max())
    idx_eq = (len(j) == max(len(old), len(mine)))
    print(f"V3 {tag}: n_committed={len(old)} n_rebuilt={len(mine)} inner={len(j)} "
          f"max|new-old|={md:.3e} {'IDENTICAL' if md < 1e-12 else 'DIFF'} "
          f"{'index-complete' if idx_eq else 'INDEX MISMATCH'}")
    out[tag] = (old, mine)

rr = BAL[BAL.index >= '2008-03-31']
print("\nV3 BAL committed, 2008-03-31+ bt.metrics.report:", M.report(rr))
print("V3 BAL rebuilt  , 2008-03-31+ bt.metrics.report:", M.report(BAL[BAL.index >= '2008-03-31']))
np.save('/tmp/vb_bal.npy', BAL.values)
BAL.to_frame('ret').to_csv('/tmp/vb_bal_rebuilt.csv')

# --- no-same-day-leak probe: same-day (leaky) throttle variant must DIFFER from committed
BAL_lk, *_ = build(0.091, 0.03, leak_variant='sameday')
AGGR_lk = BAL_lk
BAlk = ((build(0.07, 0.04, leak_variant='sameday')[0] + AGGR_lk)/2).dropna()
j = pd.concat([BAL.rename('c'), BAlk.rename('leaky')], axis=1, join='inner').dropna()
print(f"leak probe: max|committed - same-day-throttle variant| = {float((j.c-j.leaky).abs().max()):.3e} "
      f"-> committed throttle is trailing-shifted (NOT same-day)" if float((j.c-j.leaky).abs().max()) > 1e-12
      else "LEAK WARNING: same-day variant identical to committed!")
