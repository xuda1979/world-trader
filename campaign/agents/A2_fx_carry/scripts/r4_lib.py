"""A2 r4 shared mechanics: return-tilted sleeves (vt up to 15-20% documented).
All sleeves: decision-date convention (pos at t from data<=t, earn t->t+1), 6bps one-side
on turnover, vol-target trailing expanding min60d lag1. Gates per CHARTER_r4:
full SR>=0.8, halves>=0.4, <=2 neg yrs, worst yr > -6%, scramble p<0.05 (pre-vt),
plateau, ann>=12%, |corr|<=0.3 to champion daily.
"""
import sys, os
ROOT = "/Users/daxu/software/world-trader"
for p in [f"{ROOT}/campaign/harness", f"{ROOT}/campaign/scripts", f"{ROOT}/campaign/agents/A2_fx_carry/scripts"]:
    if p not in sys.path: sys.path.insert(0, p)
import numpy as np, pandas as pd
from data import fred, closes, ff_factors, ff_mom
from util import cost, vol_target, halves_ok, yearly, scramble_test
from a2_lib import _bday

CHAMP = pd.read_csv(f"{ROOT}/campaign/results/CHAMPION_FINAL_daily.csv", index_col=0, parse_dates=True).iloc[:,0]

def px_fred(name):
    return _bday(fred(name).dropna())

def run_mech(pos: pd.Series, px: pd.Series, vt: float, lag_days: int = 0):
    """pos: daily weight at decision date t (uses info<=t, optionally shifted lag_days extra).
    Returns (net_pre_vt, net_vt) decision-date series."""
    if lag_days: pos = pos.shift(lag_days)
    pos = pos.reindex(px.index).ffill().fillna(0.0)
    fr = px.pct_change().shift(-1)
    gross = (pos * fr).dropna()
    to = pos.diff().abs().fillna(0)
    net = cost(gross, to)
    return net, vol_target(net, vt).dropna()

def full_gates(r, sig=None, ret_gross=None, sr_min=0.8, half_min=0.4, max_neg=2, worst=-0.06):
    r = r.dropna()
    if len(r) < 1500: return dict(pass_=False, why=f"n={len(r)}<1500", sr=0)
    sr = r.mean()/r.std()*np.sqrt(252) if r.std() > 0 else 0
    h1, h2 = halves_ok(r)
    yr = yearly(r); neg = yr[yr<0]
    ann = r.mean()*252
    if sr < sr_min: return dict(pass_=False, sr=sr, why=f"full SR {sr:.2f}<{sr_min}")
    if h1 < half_min or h2 < half_min: return dict(pass_=False, sr=sr, h1=h1, h2=h2, why=f"halves {h1:.2f}/{h2:.2f}<{half_min}")
    if len(neg) > max_neg: return dict(pass_=False, sr=sr, why=f"negyrs {len(neg)}>{max_neg} (worst {neg.min()*100:.1f}%)")
    if len(neg) and neg.min() < worst: return dict(pass_=False, sr=sr, why=f"worst yr {neg.min()*100:.1f}%<{worst*100}%")
    annok = ann >= 0.12
    return dict(pass_=True, sr=sr, h1=h1, h2=h2, ann=ann*100, negyrs=len(neg), worst=neg.min()*100 if len(neg) else 0.0, annok=annok,
                why="" if annok else f"ann {ann*100:.1f}%<12")

def corr_to_champ(r):
    d = pd.concat([r, CHAMP], axis=1, join="inner").dropna()
    if len(d) < 500: return np.nan, len(d)
    return d.corr().iloc[0,1], len(d)

def pr(name, g, c, extra=""):
    print(f"{name:34s} SR={g.get('sr',0):5.2f} H1={g.get('h1',float('nan')):5.2f} H2={g.get('h2',float('nan')):5.2f} "
          f"ann={g.get('ann',float('nan')):5.1f}% negyr={g.get('negyrs','-')} corr={c if isinstance(c,float) and c==c else float('nan'):+.2f} "
          f"PASS={g.get('pass_')} {g.get('why','')} {extra}")
