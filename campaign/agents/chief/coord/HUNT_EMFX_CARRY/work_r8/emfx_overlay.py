"""HUNT_EMFX_CARRY R8 — SECOND WAVE (pre-registered BEFORE computation, see FINDINGS_R8.md).

O1/O2: EM-FX risk-off TIMING overlay on the champion (the only form that can clear V2 8c
given the dilution arithmetic d05 proves: a capital-diluting sleeve needs ann_s > 37.49%).

Pre-registered grid (declared before any number below was computed):
  signal  family : EW-basket  |  BRL-only      (L-day log return of long-EM direction)
  lookback L     : 21, 63, 126
  trim level to  : 0.0 (flat), 0.5 (half)
  gate           : risk-off when s_L(t) < 0  ->  g_t = to, else 1.0
  cost           : champion-identical  net_t = p_t*r_t - 6.4e-4*1.6*|p_t - p_{t-1}|, p_t=g_{t-1}
  battery        : V2 8a-8j incl. Class-A placebo (frequency+episode matched, 200 draws)

Run: python3 emfx_overlay.py    (writes emfx_overlay.json)
"""
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import emfx_lib as L
from bt.metrics import ann_geo, sharpe_d, max_dd, neg_years

COST = 6.4e-4; GEAR = 1.6
CH = L.champion(); PX = L.panel()
# NOTE: unary minus binds LOOSER than .diff(), so (-np.log(PX)).diff() == -(log-return of
# USDXXX) == the long-EM-currency log return. Writing -np.log(PX) WITHOUT .diff() gives a
# negative price LEVEL whose rolling sums are not returns at all (first run: frac(s<0)=0.996,
# an impossible gate rate that exposed it).
LRE = (-np.log(PX)).diff()             # long-EM log return increments
BASKET = LRE.mean(axis=1)              # EW across available ccy


def sig_series(fam, lb):
    if fam == "basket":
        return BASKET.rolling(lb).sum()
    return LRE["BRL"].rolling(lb).sum()


def gate(s, to):
    g = pd.Series(np.where(s < 0.0, to, 1.0), index=s.index)
    g[s.isna()] = np.nan
    return g


def overlay_net(g, r=CH):
    """pcr5_lib.overlay_net convention (champion gross 1.6 binds, so turnover is 1.6*|dp|)."""
    g = g.reindex(r.index).fillna(1.0)
    p = g.shift(1).fillna(1.0)
    to = p.diff().abs()
    if len(p):
        to.iloc[0] = abs(p.iloc[0] - 1.0)
    return p * r.fillna(0.0) - to * COST * GEAR, p


def stats(x):
    x = x.dropna(); neg, worst = neg_years(x); k = len(x)//2
    return dict(n=int(len(x)), ann=float(ann_geo(x)), sr=float(sharpe_d(x)),
                mdd=float(max_dd(x)), neg_years=int(neg), worst_year=float(worst),
                h1=float(sharpe_d(x.iloc[:k])), h2=float(sharpe_d(x.iloc[k:])))


C = stats(CH)
rng = np.random.default_rng(0)


def episodes(g, to):
    flat = (g.fillna(1.0) == to).values
    eps, run = [], 0
    for f in flat:
        if f: run += 1
        elif run: eps.append(run); run = 0
    if run: eps.append(run)
    return eps


def placebo(g, to, n=200):
    """V2 s8h Class-A instrument: frequency AND episode-length matched random trims."""
    eps = episodes(g, to)
    if not eps:
        return dict(frac_pos=np.nan, p_repro=np.nan, n_eps=0)
    m = len(CH); idx = CH.index; base = C["sr"]
    real_net, _ = overlay_net(g)
    real_dsr = sharpe_d(real_net) - base
    dsr = np.empty(n)
    for j in range(n):
        g2 = pd.Series(1.0, index=idx); pos = 0
        while pos < m:
            ln = int(eps[rng.integers(0, len(eps))])
            if pos + ln <= m: g2.iloc[pos:pos+ln] = to
            pos += ln + int(rng.integers(1, 8))
        n2, _ = overlay_net(g2)
        dsr[j] = sharpe_d(n2) - base
    return dict(dsr=dsr, frac_pos=float((dsr > 0).mean()),
                p_repro=float((dsr >= real_dsr).mean()), n_eps=int(len(eps)),
                real_dsr=float(real_dsr), eps_median=float(np.median(eps)))


OUT = {}
GRID = []
for fam in ("basket", "brl"):
    for lb in (21, 63, 126):
        for to in (0.0, 0.5):
            GRID.append((fam, lb, to))

for fam, lb, to in GRID:
    s = sig_series(fam, lb)
    g = gate(s, to)
    net, p = overlay_net(g)
    st = stats(net)
    d_ann = st["ann"] - C["ann"]; d_sr = st["sr"] - C["sr"]; d_mdd = st["mdd"] - C["mdd"]
    d_h1 = st["h1"] - C["h1"]; d_h2 = st["h2"] - C["h2"]
    trim_frac = float((g.fillna(1.0) == to).mean())
    key = "%s_L%d_to%.1f" % (fam, lb, to)
    OUT[key] = dict(lookback=lb, to=to, family=fam, trim_frac=trim_frac,
                    stats={k: round(v, 4) for k, v in st.items()},
                    d_ann=round(d_ann, 4), d_sr=round(d_sr, 4), d_mdd=round(d_mdd, 4),
                    d_h1=round(d_h1, 4), d_h2=round(d_h2, 4),
                    g8a_negy_ok=bool(st["neg_years"] == 0),
                    g8b_mdd_ok=bool(st["mdd"] > -0.07),
                    g8c_dann_ok=bool(d_ann > 0),
                    g8d_ok=bool(d_sr >= 0 and d_h2 >= 0))
    print("%-18s trim%%=%5.1f  ann %7.2f%%  SR %6.3f  MDD %6.2f%%  negy %d | "
          "dAnn %+7.2fpp  dSR %+6.3f  dMDD %+6.2fpp  dH2 %+6.3f  [8a%s 8b%s 8c%s 8d%s]" % (
              key, trim_frac*100, st["ann"]*100, st["sr"], st["mdd"]*100, st["neg_years"],
              d_ann*100, d_sr, d_mdd*100, d_h2,
              "Y" if st["neg_years"]==0 else "N", "Y" if st["mdd"]>-0.07 else "N",
              "Y" if d_ann>0 else "N", "Y" if (d_sr>=0 and d_h2>=0) else "N"))

json.dump(OUT, open(os.path.join(HERE, "emfx_overlay.json"), "w"), indent=1, default=str)
print("\nWROTE emfx_overlay.json")
