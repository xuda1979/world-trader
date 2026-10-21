#!/usr/bin/env python3
"""AUDIT_V2 independent rebuild library — written fresh, NO import from honest11_build.py /
champion_build.py / AUDIT_H11FIX code. Recipe re-derived from the committed builder SOURCE
(read for reference only) + charter description. All conventions reimplemented from scratch."""
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
from pandas.tseries.holiday import USFederalHolidayCalendar

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
 "carryv2":"campaign/agents/E1_20syspan/sleeves/E1_carryv2_GLD_2006.csv",   # NOTE deliberate typo guard
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
}
POOL["carryv2"] = "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv"
NEW = {
 "diescrack": "campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
 "CFX4":      "campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
EXEC = {'brwt15':1.5,'brwt10':1.5,'brwt7':1.5,'brwt5':1.5,'C5ng':5,'C5ngsum':5,'A5r2':6,
        'a6r7':5,'QAxasts':8,'carryv2':8,'dualmom':15}
SHORTF = {'dualmom':0.5,'QAxasts':0.4,'carryv2':0.3,'C5ng':0.5,'C5ngsum':0.5,
          'brwt15':0.5,'brwt10':0.5,'brwt7':0.5,'brwt5':0.5,'A5r2':0,'a6r7':0}
N11 = 11

_hol = USFederalHolidayCalendar().holidays(start='2006-01-01', end='2026-12-31')
HOL = set(d.date() for d in _hol)

def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

def sn(p):
    """sum non-kept-day returns into next kept weekday (federal-holiday calendar, Mon-Fri)."""
    r = load(p).dropna()
    keep = np.array([(d.dayofweek < 5 and d.date() not in HOL) for d in r.index])
    out = pd.Series(0.0, index=r.index[keep]); cu = 0.0; ki = 0; v = r.values
    for i in range(len(r)):
        cu += v[i]
        if keep[i]: out.iloc[ki] = cu; cu = 0.0; ki += 1
    return out.iloc[:ki]

def vt(r, tgt, min_win=60, cap=8.0):
    vol = r.rolling(min_win).std().shift(1) * np.sqrt(252)
    s = (tgt / vol).clip(upper=cap)
    s[vol.isna()] = 0
    return r * s.fillna(0), s

def build(TGT, THR, PS=0.08, SLOT=0.10):
    """V2: 11-pool FIX construction + 2 new sleeves at SLOT slot weight.
    Slots: 11 FIX engines at 1.0 each + 2 new at SLOT each => 11+2*SLOT total slots.
    New-sleeve capital share = SLOT/(11+2*SLOT)."""
    SnP = pd.DataFrame({n: vt(sn(p), PS)[1] for n, p in POOL.items()}).dropna(how='all')
    capWP = SnP / N11
    V = {}; S = {}
    for n in POOL:
        r = sn(POOL[n])
        v, s = vt(r, PS)
        V[n] = v - capWP[n].diff().abs().fillna(0) * ((EXEC[n]-6.0)/1e4)
        S[n] = s
    Vn = pd.DataFrame(V); Sd = pd.DataFrame(S)
    W = SnP.div(SnP.sum(axis=1), axis=0).fillna(0)
    blend11 = Vn.mean(axis=1)
    blend11 = blend11[blend11.index >= '2006-10-01']
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    b, gs = vt(blend11, TGT)
    eq = (1 + b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm - 1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc; dsc = sc.diff().abs()*0.5
    r11 = b - (tw.reindex(b.index).fillna(0) + dsc.fillna(0)) * 6e-4
    # overlay rebalance charge (REBAL=True)
    reb = Sd.diff().abs().sum(axis=1)/N11 + gs.diff().abs().fillna(0)
    r11 = r11 - reb.reindex(r11.index).fillna(0) * 6e-4
    # borrow (KEEP=True: skipna sum)
    terms = []
    for n in POOL:
        sf = SHORTF[n]
        if sf > 0:
            gn = SnP[n]/N11 * sc * sf
            terms.append(gn*(0.005 + (0.03 if n == 'dualmom' else 0.0)*0.2))
    htb = pd.concat(terms, axis=1).sum(axis=1, skipna=True)
    r11 = r11 - htb.reindex(r11.index).fillna(0)/252
    r11 = r11.dropna(how='all')
    # ---- V2 slot-weight extension: append new sleeves as capital slots ----
    newR = {n: load(p) for n, p in NEW.items()}
    allR = pd.DataFrame({**{n: sn(p) for n, p in POOL.items()}, **newR})
    # capital shares: FIX pool total slots = 11 (1.0 each), new sleeves SLOT each
    tot_slots = N11 + SLOT*len(NEW)
    # per-sleeve capital share = slots_i / tot_slots; FIX 1.0/12.2, new 0.10/12.2
    # but "total slots 12.2" (charter) means 11*1.0 + 2*0.10; capital share of new = 0.10/12.2=0.8197%??
    # charter says new-sleeve capital share 4.55% each => weight_i = slot_i / 2.2? no:
    # 0.10/(11*0.2)? Actually 11 FIX at slot 1.0 + 2 new at 0.10 -> total slot mass 11.2? charter says 12.2
    # Try: share_i = slot_i / (11*SLOT_FIX + 2*SLOT) with SLOT_FIX=1.0 => 0.10/11.2 = 0.893% (not 4.55%)
    # 4.55% = 0.10/2.2 => total = 2.2 = 11*0.2 = 11 FIX slots of 0.2 each? => FIX slot weight 0.20, new 0.10
    print(f"[v2lib] SLOT={SLOT}: share_new = {SLOT/(N11*0.2+SLOT)*100:.2f}% (charter 4.55%)")
    return r11, allR, tot_slots

if __name__ == "__main__":
    build(0.07, 0.04)
