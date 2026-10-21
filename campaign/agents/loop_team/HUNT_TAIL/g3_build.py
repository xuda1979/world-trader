#!/usr/bin/env python3
"""G3: constructive overlays on HONEST11 base blend (gross).
  1) downside-vol targeting (semivol scale, trailing-only)
  2) stress-boost: pos = 1 + w*1{vix_z>th} (T+1) — rebound capture
  3) combined
Metrics at champion level: ann(geo), SR_d, SR_m, MaxDD, worst-3y-window DD, negyrs,
mean per-sleeve-scale-equivalent leverage (gross multiple of base), turnover.
"""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_TAIL"); sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from ht_lib import honest11_blend, stats_r, ROOT
from overlay_lib import data_vix, data_spx, dd_profile

Vn, blend, Sn = honest11_blend()
blend = blend.dropna()
vix = data_vix(); spy = data_spx()
BASE_START = "2008-09-01"
COST = 6e-4

def apply_scale(sc, tag):
    """scale series applied to blend with T+1 (sc computed from data<=t, applied t+1):
    here sc is already shifted by caller. costs on |d sc|."""
    sc = sc.reindex(blend.index).fillna(0.0)
    r = blend * sc
    to = sc.diff().abs().fillna(0.0)
    net = (r - to * COST).dropna()
    net = net[net.index >= BASE_START]
    s = stats_r(net); dd = dd_profile(net)
    mean_sc = sc[sc.index >= BASE_START].mean()
    print(f"[{tag}] n={s['n']} ann={s['ann_geo']:6.2f}% SR_d={s['sr_d']:.3f} SR_m={s['sr_m']:.3f} "
          f"MaxDD={s['mdd']:6.2f}% w3y={dd['w3']:6.2f}% negyr={s['negyr']}/{s['nyr']} worst={s['worst']:6.2f}% "
          f"mean_sc={mean_sc:.3f}")
    return net, s, dd, mean_sc

# baseline: plain gross blend (no global vt)
print("== baseline: gross blend, no scale ==")
apply_scale(pd.Series(1.0, index=blend.index), "BASE_gross")
print()

# 1) downside-vol targeting
neg_ret = blend.where(blend < 0)
dvol = blend.copy()
dvol[blend >= 0] = 0.0
dd_std = dvol.rolling(60).std()  # downside-only std (trailing 60d)
tot_std = blend.rolling(60).std()
print("== downside-vol target (scale= clip(TGT/ddvol, cap); trailing 60d, shift1 T+1) ==")
for TGT in (0.06, 0.07, 0.08, 0.09, 0.10):
    for cap in (1.6, 2.0):
        sc = ((TGT / np.sqrt(252)) / dd_std).clip(0.25, cap).shift(1).fillna(0.0)
        apply_scale(sc, f"DVT_tgt{TGT}_cap{cap}")
print()

# 2) stress-boost overlay on base
v = vix.rolling(21).mean()
z = ((v - vix.rolling(252).mean())/vix.rolling(252).std()).reindex(blend.index).ffill()
print("== stress-boost: sc = 1 + w*1{z>th} (shift1) ==")
for th in (0.75, 1.0, 1.25):
    for w in (0.15, 0.25, 0.35):
        sc = (1 + w*(z > th).astype(float)).shift(1).fillna(1.0)
        apply_scale(sc, f"BOOST_th{th}_w{w}")
print()

# 3) combined: downside-vol target + stress boost
print("== combined DVT(0.08,cap1.6) x BOOST ==")
scb = (1 + 0.25*(z > 1.0).astype(float)).shift(1).fillna(1.0)
for TGT in (0.06, 0.07, 0.08):
    sc = ((TGT / np.sqrt(252)) / dd_std).clip(0.25, 1.6)
    sc = (sc * scb).shift(1).fillna(0.0)
    apply_scale(sc, f"COMBO_dvt{TGT}_b25_1.0")
