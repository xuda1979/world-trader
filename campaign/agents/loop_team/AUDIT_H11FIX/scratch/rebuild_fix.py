#!/usr/bin/env python3
"""AUDIT_H11FIX independent rebuild of GOAL100_HONEST11FIX_* — written fresh,
NO imports from campaign/scripts/honest11_build.py or champion_build.py.
Recipe from the committed builder source (read, then reimplemented)."""
import numpy as np, pandas as pd
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
N = len(POOL)
from pandas.tseries.holiday import USFederalHolidayCalendar
_hol = USFederalHolidayCalendar().holidays(start='2006-01-01', end='2026-12-31')
HOL = set(d.date() for d in _hol)

def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

def sn(p):
    """sum non-trading-day returns into the next kept weekday (federal cal, Mon-Fri)."""
    r = load(p).dropna()
    keep = np.array([(d.dayofweek < 5 and d.date() not in HOL) for d in r.index])
    out = pd.Series(0.0, index=r.index[keep]); cu = 0.0; ki = 0; v = r.values
    for i in range(len(r)):
        cu += v[i]
        if keep[i]:
            out.iloc[ki] = cu; cu = 0.0; ki += 1
    return out.iloc[:ki]

def vt(r, tgt, min_win=60, cap=8.0):
    vol = r.rolling(min_win).std().shift(1) * np.sqrt(252)
    s = (tgt / vol).clip(upper=cap)
    s[vol.isna()] = 0
    return r * s.fillna(0), s

def build(TGT, THR, PERSLEEVE=0.08, REBAL=True, KEEP=True):
    SnP = pd.DataFrame({n: vt(sn(p), PERSLEEVE)[1] for n, p in POOL.items()}).dropna(how='all')
    capWP = SnP / N
    V = {}; S = {}
    for n in POOL:
        r = sn(POOL[n])
        v, s = vt(r, PERSLEEVE)
        V[n] = v - capWP[n].diff().abs().fillna(0) * ((EXEC[n]-6.0)/1e4)
        S[n] = s
    Vn = pd.DataFrame(V); Sd = pd.DataFrame(S)
    W = SnP.div(SnP.sum(axis=1), axis=0).fillna(0)
    blend = Vn.mean(axis=1); blend = blend[blend.index >= '2006-10-01']
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    b, gs = vt(blend, TGT)
    eq = (1 + b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm - 1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc; dsc = sc.diff().abs()*0.5
    r_out = b - (tw.reindex(b.index).fillna(0) + dsc.fillna(0)) * 6e-4
    if REBAL:
        # audit-reimplementation of the overlay-rebalance charge: use the SAME scaled
        # blend b (post-global-scalar) for the global leg (see also variant B below)
        reb_g = gs.diff().abs().fillna(0)
        reb = Sd.diff().abs().sum(axis=1)/N + reb_g
        r_out = r_out - reb.reindex(r_out.index).fillna(0) * 6e-4
    terms = []
    for n in POOL:
        sf = SHORTF[n]
        if sf > 0:
            gn = SnP[n]/N * sc * sf
            terms.append(gn*(0.005 + (0.03 if n == 'dualmom' else 0.0)*0.2))
    htb = pd.concat(terms, axis=1).sum(axis=1, skipna=True) if terms else pd.Series(0.0, index=r_out.index)
    r_out = r_out - htb.reindex(r_out.index).fillna(0)/252
    return r_out.dropna(how='all'), dict(Sd=Sd, gs=gs, b=b, blend=blend, sc=sc, tw=tw, SnP=SnP, capWP=capWP, htb=htb)

def stats(r):
    eq = (1+r).cumprod(); mdd = (eq/eq.cummax()-1).min()*100
    m = (1+r).resample('ME').prod()-1
    srm = m.mean()/m.std()*np.sqrt(12); srd = r.mean()/r.std()*np.sqrt(252)
    ann = (1+r).prod()**(252/len(r))-1
    annA = r.mean()*252
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    o = r[r.index>='2017-01-01']
    return dict(n=len(r), ann=ann*100, annA=annA*100, srd=srd, srm=srm, mdd=mdd,
                neg=int((yr<0).sum()), nyrs=yr.size, worst=yr.min()*100, best=yr.max()*100,
                oos=o.mean()*252*100, srmax=60)

if __name__ == "__main__":
    A, ax = build(0.07, 0.04)
    B, bx = build(0.091, 0.03)
    BAL = ((A+B)/2).dropna()
    outs = {'SAFE': A, 'BALANCED': BAL, 'AGGRESSIVE': B}
    for v, r in outs.items():
        old = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_{v}_daily.csv",
                          index_col=0, parse_dates=True).iloc[:,0]
        j = pd.concat([old.rename('old'), r.rename('new')], axis=1, join='outer')
        both = j.dropna()
        md = float((both.old - both.new).abs().max()) if len(both) else float('nan')
        onlyold = j.index[j.old.notna() & j.new.isna()]; onlynew = j.index[j.new.notna() & j.old.isna()]
        st = stats(r)
        print(f"{v}: n_new={len(r)} n_old={old.size} overlap={len(both)} max|diff|={md:.3e} "
              f"only_old={len(onlyold)} only_new={len(onlynew)}")
        if len(onlyold): print('  sample only_old:', [str(d.date()) for d in onlyold[:5]])
        if len(onlynew): print('  sample only_new:', [str(d.date()) for d in onlynew[:5]])
        print(f"   stats: ann(geo) {st['ann']:.2f}%  ann(arith) {st['annA']:.2f}%  SR_d {st['srd']:.3f}  SR_m {st['srm']:.3f}  MDD {st['mdd']:.2f}%  neg {st['neg']}/{st['nyrs']} worst {st['worst']:.2f}% best {st['best']:.2f}%  OOS17+ {st['oos']:.2f}%")
    import pickle
    with open(f"{ROOT}/campaign/agents/loop_team/AUDIT_H11FIX/scratch/fix_state.pkl","wb") as f:
        pickle.dump({'A':A,'B':B,'BAL':BAL,'ax':ax,'bx':bx}, f)
