"""HUNT_FF_STRATARB lib: daily stat-arb / factor-timing engine on Ken French factors.
Honesty contract: T+1 (signal at t uses data<=t, earns t->t+1), 6bps/side on turnover,
no flattening, campaign-standard vt (expanding 60d min, lag1, cap3).

Factor set (all decimal daily returns):
  SMB, HML   from F-F_Research_Data_Factors_daily (L/S spreads, excess)
  MOM        from F-F_Momentum_Factor_daily (L/S spread)
  RMWop      = OP_VW 'Hi 30' - 'Lo 30'  (profitability spread, VW)
  CMAinv     = INV_VW 'Lo 30' - 'Hi 30' (investment spread: conservative minus aggressive, VW)
L/S factor spreads carry no RF leg (cash ignored, documented).
"""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
for p in [f"{ROOT}/campaign/harness"]:
    if p not in sys.path: sys.path.insert(0, p)
import data as camp_data
from util import cost, vol_target, halves_ok, yearly, scramble_test

BL16  = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv",
                    index_col=0, parse_dates=True).iloc[:,0]
BL11  = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11_daily_BALANCED_daily.csv",
                    index_col=0, parse_dates=True).iloc[:,0]

def _opinv(path):
    df = pd.read_csv(path, index_col=0)
    df = df[df.index.astype(str).str.match(r"^\d{4}-\d{2}-\d{2}$")]
    df.index = pd.to_datetime(df.index)
    return df

def factors():
    ff  = camp_data.ff_factors()          # Mkt-RF, SMB, HML, RF (decimal)
    mom = camp_data.ff_mom()              # Mom (decimal)
    op  = _opinv(f"{ROOT}/tools/quant/data/kenfrench/OP_VW_daily.csv")
    inv = _opinv(f"{ROOT}/tools/quant/data/kenfrench/INV_VW_daily.csv")
    F = pd.concat([ff[["SMB","HML"]], mom[["Mom"]],
                   (op["Hi 30"] - op["Lo 30"]).rename("RMWop"),
                   (inv["Lo 30"] - inv["Hi 30"]).rename("CMAinv")], axis=1).dropna()
    return F.sort_index()

FALL = factors()                          # 1963-07 .. 2026-06
WSTART, WEND = BL16.index.min(), FALL.index.max()   # blend-window: 2008-03-31 .. 2026-06-30
FAC = FALL.loc[(FALL.index>=WSTART)&(FALL.index<=WEND)]
FR1 = FAC.shift(-1)                        # next-day returns (T+1 booking)

def tsmom_pos(F, ks, factors=None):
    """pos[t] = mean over legs of sign(trailing k-day log return of factor, through t)."""
    factors = factors or list(F.columns)
    L = np.log1p(F[factors])
    legs = []
    for k in ks:
        sig = (L.rolling(k).sum() > 0).astype(float) - (L.rolling(k).sum() < 0).astype(float)
        legs.append(sig)
    P = pd.concat(legs).groupby(level=0).mean()
    return P[factors]

def xs_pos(F, k, top=2, bot=2):
    """cross-sectional factor momentum: long top-`top`, short bottom-`bot` by trailing k-day ret."""
    L = np.log1p(F)
    tr = L.rolling(k).sum()
    pos = pd.DataFrame(0.0, index=F.index, columns=F.columns)
    r = tr.dropna()
    for dt, row in r.iterrows():
        s = row.sort_values(ascending=False)
        for f in s.index[:top]:    pos.loc[dt, f] += 1.0/top
        for f in s.index[-bot:]:   pos.loc[dt, f] -= 1.0/bot
    return pos

def static_pos(F, wts):
    pos = pd.DataFrame(0.0, index=F.index, columns=F.columns)
    for k, v in wts.items(): pos[k] = v
    return pos

def run(pos, F=None, vt=None, cap=3.0):
    """T+1 pnl: pos decided at t (info<=t) earns t->t+1. 6bps/side on |Δpos|.
    Returns dict with gross, net, lev series (vt scaler) and net_vt."""
    F = F if F is not None else FAC
    nleg = pos.shape[1]
    fr  = F.shift(-1).reindex(columns=[c for c in pos.columns if c in F.columns]).fillna(0.0)
    gross = (pos * fr).sum(axis=1) / nleg
    to    = pos.diff().abs().sum(axis=1).fillna(0.0) / nleg
    net   = cost(gross, to)
    out = dict(gross=gross, net=net, to=to)
    if vt:
        vol = net.expanding(min_periods=60).std().shift(1) * np.sqrt(252)
        lev = (vt / vol).clip(0, cap).fillna(0.0)
        out["net_vt"] = net * lev
        out["lev"] = lev
    return out

def metrics(r):
    r = r.dropna()
    if len(r) < 100 or r.std() == 0: return dict(n=len(r), sr=0)
    yr = yearly(r)
    neg = yr[yr<0]
    dd = (1+r).cumprod(); dd = dd/dd.cummax()-1
    return dict(n=len(r), sr=r.mean()/r.std()*np.sqrt(252),
                ann=r.mean()*252*100, h1=halves_ok(r)[0], h2=halves_ok(r)[1],
                negyrs=len(neg), worst=neg.min()*100 if len(neg) else 0.0,
                maxdd=dd.min()*100)

def corr_to(r):
    d = pd.concat([r, BL16], axis=1, join="inner").dropna()
    c16 = d.corr().iloc[0,1] if len(d)>500 else np.nan
    d2 = pd.concat([r, BL11], axis=1, join="inner").dropna()
    c11 = d2.corr().iloc[0,1] if len(d2)>500 else np.nan
    return c16, c11

def flatten_gate(r):
    r = r.dropna()
    r08 = r[r.index>='2008-09-01']
    ac1 = r08.autocorr(1)
    uniqr = r08.round(10).nunique()/len(r08) if len(r08) else 0
    ac1f = r.autocorr(1)
    uniqrf = r.round(10).nunique()/len(r)
    return dict(ac1=ac1, uniqr=uniqr, ac1_full=ac1f, uniqr_full=uniqrf,
                harness_pass=(ac1<=0.5 and uniqr>=0.08),
                charter_pass=(ac1<=0.3 and uniqr>=0.5))

def scramble_p(pos, F=None, n=200, seed=7):
    """p = fraction of 200 circular-shifted-signal composites with SR >= real."""
    F = F if F is not None else FAC
    nleg = pos.shape[1]
    fr = F.shift(-1).fillna(0.0)[pos.columns]
    gross = (pos * fr).sum(axis=1)/nleg
    to = pos.diff().abs().sum(axis=1).fillna(0.0)/nleg
    net = cost(gross, to).dropna()
    rng = np.random.default_rng(seed)
    v = pos.values
    null = []
    for _ in range(n):
        k = int(rng.integers(1, len(v)))
        s = np.roll(v, k, axis=0)
        ps = pd.DataFrame(s, index=pos.index, columns=pos.columns)
        g = (ps * fr).sum(axis=1)/nleg
        t2 = ps.diff().abs().sum(axis=1).fillna(0.0)/nleg
        nn = cost(g, t2).reindex(net.index).dropna()
        null.append(nn.mean()/nn.std()*np.sqrt(252) if nn.std()>0 else 0)
    real = net.mean()/net.std()*np.sqrt(252)
    return real, float((np.array(null) >= real).mean())

def row(name, net):
    m = metrics(net); c16, c11 = corr_to(net); fg = flatten_gate(net)
    print(f"{name:30s} n={m['n']:5d} SR={m['sr']:5.2f} H1={m['h1']:5.2f} H2={m['h2']:5.2f} "
          f"ann={m['ann']:6.1f}% negy={m['negyrs']:2d} worst={m['worst']:6.1f}% DD={m['maxdd']:6.1f}% "
          f"c16={c16:+.2f} c11={c11:+.2f} ac1={fg['ac1']:+.2f} uR={fg['uniqr']:.2f} "
          f"flatH={fg['harness_pass']} flatC={fg['charter_pass']}")
    return dict(name=name, **m, c16=c16, c11=c11, **fg)
