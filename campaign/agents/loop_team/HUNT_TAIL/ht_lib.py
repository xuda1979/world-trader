"""HUNT_TAIL shared lib. Honesty contract: T+1 via shift(1), 6bps/side on turnover,
NO FLATTENING. Reuses campaign harness conventions (champion_build.vt / a5_r6_lib.build_net).
Writes ONLY under campaign/agents/loop_team/HUNT_TAIL/."""
import sys
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign/harness")
sys.path.insert(0, f"{ROOT}/campaign/scripts")
import numpy as np, pandas as pd
import data as D
from champion_build import load, vt
from a5_common import sr as sr_f, stats as stats_f, halves, scramble_pval_sig

OUT = f"{ROOT}/campaign/agents/loop_team/HUNT_TAIL"

# ---- HONEST11 pool (from frozen honest11_build.py; XGB1y flattened sleeve excluded) ----
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
 "carryv2":"campaign/agents/agents_placeholder.csv" if False else "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
}
EXEC = {'brwt15':1.5,'brwt10':1.5,'brwt7':1.5,'brwt5':1.5,'C5ng':5,'C5ngsum':5,'A5r2':6,
        'a6r7':5,'QAxasts':8,'carryv2':8,'dualmom':15}
SHORTF = {'dualmom':0.5,'QAxasts':0.4,'carryv2':0.3,'C5ng':0.5,'C5ngsum':0.5,
          'brwt15':0.5,'brwt10':0.5,'brwt7':0.5,'brwt5':0.5,'A5r2':0,'a6r7':0}

def honest11_blend():
    """Per-sleeve vt10 EW blend gross (same as honest11_build before global vt/throttle/costs).
    Returns (blend gross ret df per sleeve V, blend mean Series, Sn scale df)."""
    from pandas.tseries.holiday import USFederalHolidayCalendar
    cal = USFederalHolidayCalendar(); hol = set(cal.holidays(start='2006-01-01', end='2026-12-31').date)
    def sn(p):
        r = load(p).dropna()
        keep = np.array([(d.dayofweek < 5 and d.date() not in hol) for d in r.index])
        out = pd.Series(0.0, index=r.index[keep]); cu = 0.0; ki = 0; v = r.values
        for i in range(len(r)):
            cu += v[i]
            if keep[i]: out.iloc[ki] = cu; cu = 0.0; ki += 1
        return out.iloc[:ki]
    V, S = {}, {}
    for n in POOL:
        r = sn(POOL[n]); v, s = vt(r, 0.10); V[n] = v; S[n] = s
    Vn = pd.DataFrame(V); Sn = pd.DataFrame(S)
    blend = Vn.mean(axis=1); blend = blend[blend.index >= '2008-09-01']
    return Vn, blend, Sn

def stats_r(r):
    r = r.dropna()
    eq = (1+r).cumprod(); dd = (eq/eq.cummax()-1).min()
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    m = (1+r).resample('ME').prod()-1
    o = r[r.index>='2017-01-01']
    return dict(n=len(r), start=str(r.index.min().date()), end=str(r.index.max().date()),
        ann_geo=((1+r).prod()**(252/len(r))-1)*100,
        sr_d=float(r.mean()/r.std()*np.sqrt(252)),
        sr_m=float(m.mean()/m.std()*np.sqrt(12)),
        mdd=float(dd*100), negyr=int((yr<0).sum()), nyr=len(yr), worst=float(yr.min()*100),
        best=float(yr.max()*100),
        oos17_ann=float(o.mean()*252*100),
        yearly={int(k): round(v*100,2) for k,v in yr.items()})

def fmt_stats(tag, s):
    return (f"[{tag}] n={s['n']} {s['start']}..{s['end']} ann(geo)={s['ann_geo']:.2f}% "
            f"SR_d={s['sr_d']:.3f} SR_m={s['sr_m']:.3f} MaxDD={s['mdd']:.2f}% "
            f"negyr={s['negyr']}/{s['nyr']} worst={s['worst']:.2f}% best={s['best']:.2f}% "
            f"OOS17+ ann={s['oos17_ann']:.2f}%")

# ---- flatten gate (exact audit_harness.py logic) ----
def flatten_gate(r, start='2008-09-01'):
    r08 = r[r.index >= start].dropna()
    ac1 = float(r08.autocorr(1))
    uniqr = float(r08.round(10).nunique()/len(r08)) if len(r08)>0 else 0
    mx = float(r08.abs().max())*100
    flatten = (ac1>0.5) or (uniqr<0.08)
    return dict(ac1=ac1, uniqr=uniqr, maxabsday_pct=mx, flatten=bool(flatten))

# ---- new-sleeve gates per CHARTER ----
def sleeve_gates(net, posf, R, seed=7, nperm=200):
    s = stats_r(net); h1, h2 = halves(net)
    sp = scramble_pval_sig(posf.reindex(net.index).fillna(0.0),
                           R.reindex(net.index).fillna(0.0), n=nperm, seed=seed)
    fg = flatten_gate(net)
    ok = dict(sr=s['sr_d']>=0.6, h=(h1>=0.3) and (h2>=0.3),
              d=(s['negyr']<=2) and (s['worst']>-5.0), e=sp<=0.05,
              f=(not fg['flatten']))
    line=(f"n={s['n']} SR_d={s['sr_d']:.2f} ann={s['ann_geo']:.2f}% vol={r_vol(net):.1f}% "
          f"negyr={s['negyr']}/{s['nyr']} worst={s['worst']:.2f}% H1={h1:.2f} H2={h2:.2f} "
          f"scram_p={sp:.3f} ac1={fg['ac1']:.3f} uniqR={fg['uniqr']:.2f} "
          f"| gates a={ok['sr']} c={ok['h']} d={ok['d']} e={ok['e']} f_noflat={ok['f']}")
    return ok, line, dict(s=s, h1=h1, h2=h2, sp=sp, fg=fg)

def r_vol(r):
    r=r.dropna(); return float(r.std()*np.sqrt(252)*100)

def corr_to(r, other, minobs=250):
    j = pd.concat([r.rename('a'), other.rename('b')], axis=1, join='inner').dropna()
    if len(j) < minobs: return None, len(j)
    return float(j.corr().iloc[0,1]), len(j)
