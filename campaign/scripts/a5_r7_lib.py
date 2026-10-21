"""A5 r7 shared helpers — NEW FRED data (data_fred_new/): VIXCLS, DGS10, T10Y2Y,
TEDRATE, DAAA, DBAA (1990+). Gates per AGENT_BRIEF (strict): a SR>=0.6,
b plateau (grid neighbors >= 80% of peak), c halves>=0.3,
d <=2 neg yrs each > -5%, e scramble 200x p<=0.05, g vol-target 10% trailing-only
(a5_r6_lib.build_net convention: signal->pos, T+1 shift(1), 6bps on turnover,
expanding vol min 60d, clip 2.0). Charter mission targets: SR>=1.0, corr<0.25."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import data as D
from a5_common import sr, stats, halves, scramble_pval_sig
from a5_r6_lib import build_net, corr_table, load_lib_csv, spy_returns_2000

FREDNEW = f"{D.ROOT}/tools/quant/hedge_fund_strats/data_fred_new"

def fred_new(name):
    df = pd.read_csv(f"{FREDNEW}/{name}.csv", index_col=0, parse_dates=True)
    s = pd.to_numeric(df.iloc[:, 0], errors="coerce")
    return s[~s.index.duplicated(keep="last")].sort_index().ffill()

def spy93():
    """Spliced SPY returns 1993-01..2026-08 (FRED spy_early price proxy pre-2006,
    twelve_big SPY after; seam-day return nulled). Conservative: pre-2006 leg
    excludes dividends."""
    r, _ = spy_returns_2000()
    return r.dropna()

A5_OWN = ["A5_r2_contango_rateshock", "A5_r4_vt15_contango"]

def corr_all(net):
    ct = corr_table(net, topn=5)
    own = {}
    for nm in A5_OWN:
        try:
            p = f"{D.ROOT}/campaign/agents/A5_vol_cond/sleeves/{nm}.csv"
            l = pd.read_csv(p, index_col=0, parse_dates=True).iloc[:, 0].astype(float)
            j = pd.concat([net, l], axis=1, join="inner").dropna()
            if len(j) >= 250: own[nm] = round(float(j.corr().iloc[0, 1]), 2)
        except Exception: pass
    return ct, own

def gates_r7(name, net, posf, R, extra=""):
    s = stats(net); h1, h2 = halves(net)
    sp = scramble_pval_sig(posf.reindex(net.index).fillna(0.0),
                           R.reindex(net.index).fillna(0.0), n=200, seed=7)
    ok = dict(a=s["sr"] >= 0.6, c=(h1 >= 0.3) and (h2 >= 0.3),
              d=(s["neg_yr"] <= 2) and (s["worst"] > -5.0), e=sp <= 0.05)
    line = (f"[{name}] n={s['n']} SR={s['sr']:.2f} ann={s['ann']:.2f}% vol={s['vol']:.1f}% "
            f"negyr={s['neg_yr']}/{s['n_yr']} worst={s['worst']:.1f}% H1={h1:.2f} H2={h2:.2f} "
            f"scram_p={sp:.3f} | a={ok['a']} c={ok['c']} d={ok['d']} e={ok['e']} {extra}")
    return ok, line, s

def hysteresis_pos(z, th, hyst):
    """state=1 when z<th (enter calm), state=0 when z>th+hyst (exit stress)."""
    zv = z.values; out = np.zeros(len(zv)); st = 0.0
    for t in range(len(zv)):
        zz = zv[t]
        if not np.isnan(zz):
            if zz < th: st = 1.0
            elif zz > th + hyst: st = 0.0
        out[t] = st
    return pd.Series(out, index=z.index)

def neighbors(best, keys):
    ths = sorted({k[0] for k in keys}); hys = sorted({k[1] for k in keys})
    i, j = ths.index(best[0]), hys.index(best[1]); out = []
    if i > 0: out.append((ths[i - 1], best[1]))
    if i < len(ths) - 1: out.append((ths[i + 1], best[1]))
    if j > 0: out.append((best[0], hys[j - 1]))
    if j < len(hys) - 1: out.append((best[0], hys[j + 1]))
    return out

def synth_tr(yield_pct, dur):
    """Constant-duration total-return synth from a yield level series (%):
    TR_t = dur * (-dy_t) + y_t/252 (per day). dy in decimal."""
    y = yield_pct / 100.0
    return dur * (-y.diff()) + y / 252.0
