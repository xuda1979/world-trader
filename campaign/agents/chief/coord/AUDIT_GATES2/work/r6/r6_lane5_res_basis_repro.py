#!/usr/bin/env python3
"""AUDIT_GATES2 R6 lane 5 — RES_BASIS row-137 standalone-PASS recompute (docs-only audit).

Recomputes, from published artifacts + on-disk data only (no RES_BASIS module imports):
  1. sleeve CSV sha vs meta pin (da0285b9...)
  2. the recipe rebuild (hunt_r1.py recipe re-implemented independently, my own code):
     log(DHOILNYH*42 / DCOILBRENTEU), z=(x-m1.shift(1))/s1.shift(1) win63, hysteresis
     z_in=1.0 z_out=1.0 meanrev, dollar-neutral 2-leg, T+1, vt 0.08/cap3 on gross,
     6.4bps full|dW| + 0.5%/yr borrow  -> byte-compare vs published sleeve ret column
  3. every meta gate number: NET SR/ann/MDD/H1/H2/negyrs/worst, corr_champ, ac1, uniqR,
     IS/OOS, T+2 decay, cost ladder, blend w=0.25 (dSR +0.199, dAnn +4.21pp, MDD -6.64%,
     dH2 +0.048), plateau grids, pre-2008 probe
  4. the FULL V2 battery re-run (gates.run r=per-unit sig=We['a'], leak_check=True,
     beats_passive=True + pinned trio) -> v2sr 1.6031, leak stats, scr_p 0.0, bp 1.603
  5. §10a scramble reproducibility from the published artifact: the sleeve CSV is
     [date,ret] only (no positions column) -> scramble claims are agent-run only
     unless positions are recoverable from the recipe (they are, via the rebuild).
"""
import sys, hashlib
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
import bt.gates as bgates
from bt.metrics import sharpe_d, half_split, neg_years, ann_geo, max_dd
from bt.engine import vol_target_scale, cost_turnover, borrow_cost

ROOT = "/Users/daxu/software/world-trader"
SLV = f"{ROOT}/campaign/team/agents/RES_BASIS/sleeves"
NEW = f"{ROOT}/tools/quant/data/newdata"
GAL = 42.0

def load(path, col=None):
    s = pd.read_csv(path, index_col=0, parse_dates=True)
    s = s[col].astype(float) if col and col in s.columns else s.iloc[:, 0].astype(float)
    return s[~s.index.duplicated(keep='last')].sort_index()

# ---------- 1. artifact identity ----------
raw = open(f"{SLV}/RB_hobr_crack_hyst_w63_z10_zo10.csv", 'rb').read()
sha = hashlib.sha256(raw).hexdigest()
pub = load(f"{SLV}/RB_hobr_crack_hyst_w63_z10_zo10.csv", 'ret')
print(f"[1] sleeve sha256={sha[:16]} (meta pin da0285b9a7a5e6a2 -> match={sha.startswith('da0285b9a7a5e6a2')})")
print(f"    published rows={len(pub)} span {pub.index[0].date()}..{pub.index[-1].date()}")

# ---------- 2. independent recipe rebuild (truncated to the published span end) ----------
# NOTE: DHOILNYH/DCOILBRENTEU rotated 2026-09-08 14:07 (after the sleeve was built);
# truncate to the sleeve's own end date so the rebuild is judged on its declared vintage.
ho = load(f"{NEW}/DHOILNYH.csv"); br = load(f"{NEW}/DCOILBRENTEU.csv")
j = pd.concat({'a': ho * GAL, 'b': br}, axis=1).dropna()
j = j[(j > 0).all(axis=1)]
j = j[j.index >= '2008-01-01']
j = j[j.index <= pub.index[-1]]
sp = np.log(j['a'] / j['b'])
r_a = j['a'].pct_change(); r_b = j['b'].pct_change()

win, z_in, z_out = 63, 1.0, 1.0
m = sp.rolling(win, min_periods=win // 2).mean().shift(1)
s = sp.rolling(win, min_periods=win // 2).std().shift(1)
z = ((sp - m) / s.replace(0, np.nan)).where(s.notna())
idx = z.dropna().index
z = z.reindex(idx)

st = np.zeros(len(z)); cur = 0.0
for i, zv in enumerate(z.values):
    if not np.isfinite(zv):
        st[i] = cur
    elif cur == 0.0:
        if zv > z_in: cur = 1.0
        elif zv < -z_in: cur = -1.0
        st[i] = cur
    elif cur == 1.0 and zv < z_out:
        cur, st[i] = 0.0, 0.0
    elif cur == -1.0 and zv > -z_out:
        cur, st[i] = 0.0, 0.0
    else:
        st[i] = cur
st = pd.Series(st, index=idx)
W = pd.DataFrame({'a': -st, 'b': st}, index=idx)   # meanrev: a=-st, b=+st
r_a = r_a.reindex(idx).fillna(0.0); r_b = r_b.reindex(idx).fillna(0.0)
R = pd.concat({'a': r_a, 'b': r_b}, axis=1)

We = W.shift(1).fillna(0.0)
gross = (We * R).sum(axis=1)
vts = vol_target_scale(gross.to_frame('g'), target=0.08, cap=3.0)['g']
We_vt = We.mul(vts, axis=0)
port = (We_vt * R).sum(axis=1)
net = (port - cost_turnover(We_vt, cost_bps=6.4) - borrow_cost(We_vt)).rename('ret')

live = (We_vt.fillna(0) != 0).any(axis=1)
net = net[net.index >= live.idxmax()]
print(f"[2] rebuild n={len(net)} {net.index[0].date()}..{net.index[-1].date()} "
      f"(published n={len(pub)} {pub.index[0].date()}..{pub.index[-1].date()})")
if len(net) == len(pub):
    dev = float(np.abs(net.values - pub.values).max())
    print(f"    max|dev| vs published ret column = {dev:.3e}  (byte-repro: {dev == 0.0})")
else:
    dev = None
    print(f"    !! row-count mismatch vs published — index diff: "
          f"{len(set(pub.index) - set(net.index))} pub-only, {len(set(net.index) - set(pub.index))} mine-only")

# ---------- 3. meta gate numbers ----------
def block(name, r):
    h1, h2 = half_split(r); neg, worst = neg_years(r)
    print(f"    {name}: SR={sharpe_d(r):.4f} ann={ann_geo(r)*100:.2f}% MDD={max_dd(r)*100:.2f}% "
          f"H1={h1:.3f} H2={h2:.3f} neg={neg} worst={worst*100:.2f}%")

print("[3] meta numbers (claimed -> recomputed):")
print("    claimed NET: SR=1.3498 ann=13.25% MDD=-22.29% H1=2.182 H2=0.753 neg=1/18 worst=-0.69%(2022) "
      "corr=+0.0219 ac1=-0.1083 uniqR=0.6038")
block("rebuilt", net)
champ = load(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv", 'ret')
print(f"    corr_champ claimed +0.0219 -> recomputed {bgates.corr_to(champ, net):+.4f}")
print(f"    ac1 claimed -0.1083 -> {net.autocorr(1):+.4f} | uniqR claimed 0.6038 -> "
      f"{(net.round(10).nunique()/len(net)):.4f}")
isr = net[net.index < '2017-01-01']; oos = net[net.index >= '2017-01-01']
print(f"    IS/OOS claimed 2.145/0.807 -> {sharpe_d(isr):.3f}/{sharpe_d(oos):.3f}")

print("    cost ladder claimed 6.4/10/20bps -> SR 1.350/1.211/0.823")
for bps in (6.4, 10.0, 20.0):
    n2 = port - cost_turnover(We_vt, cost_bps=bps) - borrow_cost(We_vt)
    n2 = n2[n2.index >= net.index[0]]
    print(f"      {bps}bps: SR={sharpe_d(n2):.3f}")

print("    blend w=0.25 claimed dSR +0.199 dAnn +4.21pp MDD -6.64% neg 0 dH2 +0.048")
for w in (0.10, 0.25, 0.35, 0.50):
    b = champ + net.reindex(champ.index).fillna(0.0) * w
    h1b, h2b = half_split(b); h1c, h2c = half_split(champ)
    negb, _ = neg_years(b)
    print(f"      w={w}: dSR={sharpe_d(b)-sharpe_d(champ):+.3f} "
          f"dAnn={(ann_geo(b)-ann_geo(champ))*100:+.2f}pp MDD={max_dd(b)*100:.2f}% "
          f"neg={negb} dH2={h2b-h2c:+.3f}")

# ---------- 4. FULL V2 battery re-run ----------
print("[4] V2 battery re-run (claimed v2sr=1.6031 leak_corr +0.1071 p 2.74e-13 "
      "lag_scan -2:-0.1095 -1:-0.1885 0:+0.1071 1:+0.0264 2:+0.0185 scr_p=0.0 bp 1.603 vs 0.602)")
rpu = (r_a - r_b)
# emit_sleeve.py truncates We + rpu to the first LIVE day before the battery — mirror that.
bat_idx = We_vt.index[We_vt.index >= net.index[0]]
v2 = bgates.run(rpu.reindex(bat_idx).fillna(0.0), ref=champ,
                sig=We_vt['a'].reindex(bat_idx).fillna(0.0), scramble_n=200,
                beats_passive=True,
                spy=load(f"{ROOT}/tools/quant/data/twelvedata/SPY.csv", 'close').pct_change(),
                ief=load(f"{ROOT}/tools/quant/data/more_etf/IEF.csv", 'close').pct_change(),
                cta=load(f"{ROOT}/campaign/results/sleeve_library/CTA_15vol.csv", 'ret'))
lp = v2['leak']; bp = v2['beats_passive']
ls_ = ' '.join(f"{k}:{v:+.4f}" for k, v in sorted(lp['lag_scan'].items()))
print(f"    v2sr={v2['sr']:.4f} v2corr={v2['corr']:+.4f} leak_corr={lp['same_period_corr']:+.4f} "
      f"p={lp['same_period_p']:.2e} lag_scan {ls_} leak_ok={v2['leak_ok']}")
print(f"    scr_p={v2['scr_p']} bp_best={bp['best_passive_name']}:{bp['best_passive_sr']:.3f} "
      f"bp_ok={v2['beats_passive_ok']} composite PASS={v2['pass']}")

# ---------- 5. plateau grids (claimed w: 1.356/1.357/1.350/1.302/1.148 ok@63 thr 1.086;
#                z_in: peak 1.350@1.0 nb 1.310/1.247 thr 1.080) ----------
print("[5] plateau grids")
def sr_for(win_, zi_, zo_=1.0):
    m2 = sp.rolling(win_, min_periods=win_ // 2).mean().shift(1)
    s2 = sp.rolling(win_, min_periods=win_ // 2).std().shift(1)
    z2 = ((sp - m2) / s2.replace(0, np.nan)).where(s2.notna())
    ix = z2.dropna().index
    z2 = z2.reindex(ix)
    s2t = np.zeros(len(z2)); cur2 = 0.0
    for i, zv in enumerate(z2.values):
        if not np.isfinite(zv): s2t[i] = cur2
        elif cur2 == 0.0:
            if zv > zi_: cur2 = 1.0
            elif zv < -zi_: cur2 = -1.0
            s2t[i] = cur2
        elif cur2 == 1.0 and zv < zo_: cur2, s2t[i] = 0.0, 0.0
        elif cur2 == -1.0 and zv > -zo_: cur2, s2t[i] = 0.0, 0.0
        else: s2t[i] = cur2
    W2 = pd.DataFrame({'a': -s2t, 'b': s2t}, index=ix)
    ra2 = j['a'].pct_change().reindex(ix).fillna(0.0)
    rb2 = j['b'].pct_change().reindex(ix).fillna(0.0)
    R2 = pd.concat({'a': ra2, 'b': rb2}, axis=1)
    We2 = W2.shift(1).fillna(0.0)
    g2 = (We2 * R2).sum(axis=1)
    sc = vol_target_scale(g2.to_frame('g'), target=0.08, cap=3.0)['g']
    We2 = We2.mul(sc, axis=0)
    n2 = ((We2 * R2).sum(axis=1) - cost_turnover(We2, cost_bps=6.4) - borrow_cost(We2))
    live2 = (We2.fillna(0) != 0).any(axis=1)
    return sharpe_d(n2[n2.index >= live2.idxmax()])

wgrid = {w: round(sr_for(w, 1.0), 3) for w in (21, 40, 63, 90, 126)}
print(f"    window grid {wgrid} (claimed 1.356/1.357/1.350/1.302/1.148)")
okw, infow = bgates.plateau_ok(wgrid, 63)
print(f"    plateau@63 ok={okw} nb={ {k: round(v,3) for k,v in infow['neighbors'].items()} } "
      f"thr={infow['threshold']:.3f} (claimed thr 1.086)")
zgrid = {zz: round(sr_for(63, zz), 3) for zz in (0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0)}
print(f"    z_in grid {zgrid}")
okz, infoz = bgates.plateau_ok(zgrid, 1.0)
print(f"    plateau@1.0 ok={okz} nb={ {k: round(v,3) for k,v in infoz['neighbors'].items()} } "
      f"thr={infoz['threshold']:.3f} (claimed nb 1.310/1.247 thr 1.080)")

print(f"[5b] §10a: published artifact carries positions? ",
      f"{list(pd.read_csv(f'{SLV}/RB_hobr_crack_hyst_w63_z10_zo10.csv').columns)} — "
      f"ret-only; scramble claim is recipe-verifiable via this rebuild")
