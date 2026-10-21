#!/usr/bin/env python3
"""DAILY-FREQUENCY audit of the AP gold champion (monthly rebalance).

The champion's MaxDD (-14.2%) was computed on MONTHLY returns; the
investor's account moves DAILY between monthly rebalances. This rebuilds
the same book (composite momentum top-quartile + 30% 2mo-reversal LS +
SPY10MA gate + VIX-level de-risk + gold 0.2, vol-target 12% + DD reducer
at monthly cadence) but records DAILY returns of the held book, giving
the honest daily MaxDD and SR.

Signals and gates are evaluated at month-ends exactly as the champion
does; the book is carried between rebalances.

Usage: python run_champion_daily_audit.py
"""
from __future__ import annotations
import os, sys, glob
import numpy as np
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
import risk_gate as rg
BIG_DIR = os.path.join(HERE, "..", "tools", "quant", "data", "twelve_big")
GLD_CSV = os.path.join(HERE, "..", "tools", "quant", "data", "twelvedata", "GLD.csv")
START_YM = os.environ.get("START_YM", "2008-01")
GOLD_W = float(os.environ.get("GOLD_W", 0.2))
VOL_TARGET = float(os.environ.get("VOL_TARGET", 0.12))
REV_SLEEVE = float(os.environ.get("REV_SLEEVE", 0.3))

def build_daily():
    files = sorted(glob.glob(os.path.join(BIG_DIR, "*.csv")))
    all_d = {}
    for f in files:
        sym = os.path.basename(f).replace(".csv", "")
        try:
            df = pd.read_csv(f, index_col=0, parse_dates=True)
            c = "close" if "close" in df.columns else df.columns[0]
            s = df[c].astype(float)
            all_d[sym] = s[~s.index.duplicated(keep="last")]
        except Exception:
            continue
    px = pd.DataFrame(all_d).sort_index()
    px = px[~px.index.duplicated(keep="last")].ffill()
    return px

def main() -> None:
    print("Building daily panel...", flush=True)
    px = build_daily()
    pxm = px.resample("ME").last()                       # monthly closes for signals
    print(f"daily panel: {px.index[0].date()}..{px.index[-1].date()} {px.shape[1]} names", flush=True)
    # daily forward returns of the held book (names + gold)
    dret = px.pct_change()
    gld = pd.read_csv(GLD_CSV, index_col=0, parse_dates=True)
    gc = "close" if "close" in gld.columns else gld.columns[0]
    gld_d = gld[gc].astype(float)
    gld_ret = gld_d.pct_change().reindex(px.index).fillna(0.0)

    fwd_m = pxm.pct_change(1).shift(-1)                  # monthly fwd (signal months)
    comp = (pxm.pct_change(3) + pxm.pct_change(6) + pxm.pct_change(12)) / 3
    rev = -pxm.pct_change(2)
    spy = rg.load_daily("SPY")
    spy_m = spy.resample("ME").last()
    vix = rg.load_daily("vix").resample("ME").last()

    months = [d for d in pxm.index if d.strftime("%Y-%m") >= START_YM]
    daily_ret_all = []
    daily_dates = []
    eq, peak = 1.0, 1.0
    month_ret_series = []                                 # monthly vol-target inputs
    for mi, dt in enumerate(months):
        # ---- month-end signals (identical to the champion) ----
        g = 1.0 if float(spy_m.asof(dt)) >= spy_m[spy_m.index <= dt].tail(10).mean() else 0.0
        v = float(vix.asof(dt)) if pd.notna(vix.asof(dt)) else 20
        vg = 0.3 if v > 30 else (0.5 if v > 25 else (0.75 if v > 20 else 1.0))
        s = comp.loc[dt].dropna()
        fr = fwd_m.loc[dt].dropna()
        valid = s.index.intersection(fr.index)
        if len(valid) < 20:
            mom_names, mom_ret = [], 0.0
        else:
            G = max(1, len(valid) // 4)
            top = list(s.loc[valid].sort_values(ascending=False).index[:G])
            mom_names = top
        s2 = rev.loc[dt].dropna()
        fr2 = fwd_m.loc[dt].dropna()
        valid2 = s2.index.intersection(fr2.index)
        if len(valid2) >= 20:
            G2 = max(1, len(valid2) // 4)
            r2 = s2.loc[valid2].sort_values(ascending=False)
            rev_long = list(r2.index[:G2]); rev_short = list(r2.index[-G2:])
        else:
            rev_long = rev_short = []
        # vol-target + DD reducer (monthly cadence, same as champion)
        scale = 1.0
        if mi >= 6:
            rv = np.std(month_ret_series[-6:]) * np.sqrt(12) + 1e-6
            scale = min(VOL_TARGET / rv, 1.5)
            dd = eq / peak - 1
            if dd < -0.12: scale *= 0.25
            elif dd < -0.08: scale *= 0.5
        w = (1 - GOLD_W) * scale * vg
        # ---- carry the book through the month's days ----
        nxt = months[mi + 1] if mi + 1 < len(months) else None
        days = px.index[(px.index > dt) & (px.index <= (nxt if nxt is not None else px.index[-1]))]
        month_cum = 1.0
        for d in days:
            dr = 0.0
            if mom_names:
                r = dret.loc[d, mom_names].mean() if d in dret.index else 0.0
                dr += g * w * (r if pd.notna(r) else 0.0)
            if rev_long:
                rl = dret.loc[d, rev_long].mean() if d in dret.index else 0.0
                rs = dret.loc[d, rev_short].mean() if d in dret.index else 0.0
                dr += w * REV_SLEEVE * ((rl if pd.notna(rl) else 0.0) - (rs if pd.notna(rs) else 0.0))
            gr = float(gld_ret.loc[d]) if d in gld_ret.index else 0.0
            dr += GOLD_W * gr
            daily_ret_all.append(dr)
            daily_dates.append(d)
            eq *= (1 + dr); peak = max(peak, eq)
            month_cum *= (1 + dr)
        month_ret_series.append(month_cum - 1)
    pd.Series(daily_ret_all, index=pd.DatetimeIndex(daily_dates)).to_csv(
        os.path.join(HERE, "data", "wf_champion_gold_opt_daily.csv"))
    r = np.array(daily_ret_all)
    sr = r.mean() / r.std() * np.sqrt(252)
    ann = r.mean() * 252 * 100
    eq2 = np.cumprod(1 + r)
    dd = min(eq2 / np.maximum.accumulate(eq2) - 1) * 100
    print(f"DAILY audit: SR={sr:.3f} ret={ann:+.2f}% vol={r.std()*np.sqrt(252)*100:.2f}% MaxDD={dd:.2f}% n={len(r)}d")
    # monthly comparison
    mr = np.array(month_ret_series)
    sr_m = mr.mean() / mr.std() * np.sqrt(12)
    eqm = np.cumprod(1 + mr)
    dd_m = min(eqm / np.maximum.accumulate(eqm) - 1) * 100
    print(f"MONTHLY same book: SR={sr_m:.3f} ret={mr.mean()*12*100:+.2f}% MaxDD={dd_m:.2f}% (champion claims 1.086/14.1%/-14.2%)")

if __name__ == "__main__":
    main()
