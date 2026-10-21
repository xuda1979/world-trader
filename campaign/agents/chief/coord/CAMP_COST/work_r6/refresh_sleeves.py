#!/usr/bin/env python3
"""CAMP_COST R6 charter (b): refresh stale sleeves toward 2026-09-05.

Two steps per sleeve, per the R2/R3 protocol:
  1. BYTE-RECON the committed/costfix bytes from live sources under the documented
     convention (gate: maxdev < 1e-12 on the overlap, index equality). If this fails,
     the sleeve CANNOT be refreshed (data-vintage drift) and we stop for that sleeve.
  2. EMIT the same generator on CURRENT sources, echoed on the committed index EXTENDED
     with the new tail rows (cost stream only; no relabeling of history). Written to
     work_r6/refresh/<name>__refresh.csv -- NEVER overwriting the committed builder
     inputs (__costfix.csv are rawew13v2_build PATHS entries).

Sleeves: brwt10_2000 / brwt7 / brwt5 (brwt5_2000 excluded: not a champion slot),
         diescrack_L40Z20 (champion slot via rawew13v2_build NEW).

Usage: python3 refresh_sleeves.py
"""
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = ROOT + "/campaign/agents/chief/coord/CAMP_COST/work_r6/refresh"
sys.path.insert(0, ROOT + "/campaign/agents/B2_highfreq")
from gates import vol_target as vt_b2  # noqa: E402  (brwt family vt)

FRED = ROOT + "/tools/quant/hedge_fund_strats/data_fred"
EIA = ROOT + "/tools/quant/data/eia_weekly"
NEW = ROOT + "/tools/quant/data/newdata"


def _load(p, col=None):
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    v = df[col] if col and col in df.columns else df.iloc[:, 0]
    return pd.to_numeric(v, errors="coerce").dropna()


def fred(name, src=FRED):
    s = _load(f"{src}/{name}.csv")
    return s[~s.index.duplicated(keep="last")].sort_index()


# ------------------------------------------------------------------ brwt family
def brwt_load():
    """FRED brent/wti spliced with EIA tail (byte-identical overlap, R3-proven)."""
    BR = fred("brent")
    WT = fred("wti")
    E_BR = _load(f"{EIA}/brent_spot_daily.csv")
    E_WT = _load(f"{EIA}/wti_spot_daily.csv")
    BR = pd.concat([BR, E_BR[E_BR.index > BR.index[-1]]])
    WT = pd.concat([WT, E_WT[E_WT.index > WT.index[-1]]])
    return BR, WT


def brwt_build(lb, zb, min_start):
    BR, WT = brwt_load()
    sp = (np.log(BR) - np.log(WT)).dropna()
    sp = sp[sp.index >= min_start]
    m = sp.rolling(lb, min_periods=lb).mean()
    sd = sp.rolling(lb, min_periods=lb).std().replace(0, np.nan)
    z = (sp - m) / sd
    pos = pd.Series(0.0, index=sp.index)
    pos[z < -zb] = 1.0
    pos[z > zb] = -1.0
    gross = pos * sp.diff().shift(-1)
    net = gross - pos.diff().abs() * 6.4 / 1e4        # FULL |dW| @ 6.4bps
    scaled, _ = vt_b2(net)
    return scaled


# ------------------------------------------------------------------ diescrack
def diescrack_build():
    dj = fred("DJFUELUSGULF", src=NEW)
    wt = fred("wti_full")
    # wti_full (FRED harness file) lags at 2026-08-11; EIA wti_spot_daily runs to 2026-09-01
    # and is byte-identical on the overlap (maxdiff 0.000000, n=10221) — the same splice
    # license proven for brent/wti in R3. Diesel (newdata) ends 2026-08-25 => refresh bound.
    E_WT = _load(f"{EIA}/wti_spot_daily.csv")
    wt = pd.concat([wt, E_WT[E_WT.index > wt.index[-1]]])
    sp = (np.log(dj * 42.0) - np.log(wt)).dropna()
    sp = sp[sp.index >= "2008-01-01"]
    m = sp.rolling(40, min_periods=40).mean()
    sd = sp.rolling(40, min_periods=40).std().replace(0, np.nan)
    z = (sp - m) / sd
    pos = pd.Series(0.0, index=sp.index)
    pos[z < -2.0] = 1.0
    pos[z > 2.0] = -1.0
    ret = sp.diff().shift(-1)
    gr = (pos * ret).dropna()
    tup = pos.diff().abs().reindex(gr.index).fillna(0.0)
    base = gr - tup * 6.4 / 1e4
    pi = pos.reindex(base.index).fillna(0.0)
    bmask = ((pi != 0) | (pi.shift(1).fillna(0) != 0)).astype(float)
    sc = (0.08 / (base.expanding(60).std() * np.sqrt(252))).clip(upper=3.0)
    return ((base * sc).fillna(0.0) - bmask * 0.005 / 252).dropna()


TARGETS = {
    "brwt10": lambda: brwt_build(10, 1.0, "2000-01-01"),
    "brwt7": lambda: brwt_build(7, 1.0, "2008-01-01"),
    "brwt5": lambda: brwt_build(5, 1.0, "2008-01-01"),
    "diescrack": diescrack_build,
}
COMMITTED = {
    "brwt10": ROOT + "/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
    "brwt7": ROOT + "/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
    "brwt5": ROOT + "/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
    "diescrack": ROOT + "/campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
}


def stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    return (f"n={len(r)} ann={((1+r).prod()**(252/len(r))-1)*100:.3f}% "
            f"sr={r.mean()/r.std(ddof=1)*np.sqrt(252):.4f} "
            f"mdd={float((nav/nav.cummax()-1).min())*100:.2f}%")


def main():
    import os
    os.makedirs(OUT, exist_ok=True)
    for name, fn in TARGETS.items():
        gen = fn()
        committed = pd.read_csv(COMMITTED[name], index_col=0, parse_dates=True).iloc[:, 0]
        committed = pd.to_numeric(committed, errors="coerce")
        j = pd.concat([committed.dropna().rename("c"), gen.rename("g")],
                      axis=1, join="inner").dropna()
        dev = float((j.c - j.g).abs().max())
        recon_ok = len(j) == int(committed.notna().sum()) and dev < 1e-12
        tail = gen[gen.index > committed.dropna().index.max()].dropna()
        print(f"[{name}] recon inner={len(j)} maxdev={dev:.3e} "
              f"{'OK' if recon_ok else 'FAIL-> cannot refresh'}")
        print(f"[{name}] committed end {committed.dropna().index.max().date()} "
              f"new tail rows {len(tail)}"
              + (f" to {tail.index.max().date()}" if len(tail) else " (source-limited)"))
        if not recon_ok or len(tail) == 0:
            continue
        # echo committed index + append the new tail (cost stream only, no history relabel)
        out = pd.concat([committed, tail])
        assert out.index.is_unique and out.index.is_monotonic_increasing
        path = f"{OUT}/{name}__refresh.csv"
        pd.DataFrame({"ret": out.values}, index=out.index).rename_axis("date") \
          .to_csv(path, na_rep="")
        oldv = committed.dropna()
        print(f"[{name}] refresh stats: committed {stats(oldv)} | extended {stats(gen)}")
        print(f"[{name}] wrote {path} rows={len(out)} (valid {int(out.notna().sum())})")


if __name__ == "__main__":
    main()
