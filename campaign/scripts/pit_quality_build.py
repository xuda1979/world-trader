#!/usr/bin/env python3
"""PIT-clean cross-sectional equity quality/profitability sleeve builder.

Uses SEC EDGAR XBRL cached fundamentals (503 stocks, filed-dates preserved) to build a
POINT-IN-TIME quality (profitability) metric that is EXACTLY as it appeared on each date
(the `filed` date = when the value became public, no restatement lookahead). Then ranks
stocks cross-sectionally each month, longs the top-profitability quintile and shorts the
bottom, earning next-month returns T+1 from twelve_big close prices.

This is lever #1 of the "improve the champion" goal: the ONE genuinely untested family,
now built PIT-clean (vs the restated 2016+ model panel used in prior audits).
"""
import json, glob, os, sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
CACHE = f"{ROOT}/alphaportfolio_replication/data/sec_fundamentals_cache"
PRICE = f"{ROOT}/tools/quant/data/twelve_big"
OUT = f"{ROOT}/campaign/agents/CHAMP_HUNT_FUND/sleeves/PIT_quality_ls_daily.csv"

def load_facts():
    rows = []
    files = sorted(glob.glob(f"{CACHE}/*.json"))
    for f in files:
        sym = os.path.basename(f).split('_')[0]
        try:
            d = json.load(open(f))
        except Exception:
            continue
        gaap = d.get("facts", {}).get("us-gaap", {})
        for tag in ("NetIncomeLoss", "StockholdersEquity", "Revenues"):
            t = gaap.get(tag)
            if not t:
                continue
            for units, facts in t.get("units", {}).items():
                for x in facts:
                    filed = x.get("filed"); end = x.get("end"); val = x.get("val")
                    if filed and end and val is not None:
                        rows.append(dict(sym=sym, tag=tag, filed=filed, end=end, val=val))
    df = pd.DataFrame(rows)
    df["filed"] = pd.to_datetime(df["filed"])
    df["end"] = pd.to_datetime(df["end"])
    return df

def pit_metric_panel(facts, month_ends):
    """At each month-end t, for each stock take the most recently FILED value of each tag
    (net income, equity) and form ROE = NI/Equity. PIT: only facts with filed <= t, and to
    avoid restatement-peeking we take the value of the LATEST period-end that had been filed;
    for a same tag we keep the fact with max filed<=t (latest as publicly known)."""
    recs = []
    facts_sorted = facts.sort_values("filed")
    by_sym = {s: g for s, g in facts_sorted.groupby("sym")}
    for t in month_ends:
        for sym, g in by_sym.items():
            # facts known (filed) by t
            known = g[g["filed"] <= t]
            if known.empty:
                continue
            # For each tag, the value as publicly known at t = the value of the LATEST
            # period-end that had been filed by t (this is the temporal rollback).
            roe = None; rev = None
            kn_ni = known[known["tag"] == "NetIncomeLoss"]
            kn_eq = known[known["tag"] == "StockholdersEquity"]
            # latest period-end among all known facts
            if not kn_ni.empty and not kn_eq.empty:
                # use the facts with the latest 'end' that were filed by t
                latest_end_ni = kn_ni["end"].max()
                latest_end_eq = kn_eq["end"].max()
                # NI and Equity must refer to the same period for a meaningful ROE:
                # take both at min(latest_end_ni, latest_end_eq) period
                pe = min(latest_end_ni, latest_end_eq)
                ni_rows = kn_ni[kn_ni["end"] == pe]
                eq_rows = kn_eq[kn_eq["end"] == pe]
                # choose the most recently filed among ties
                if not ni_rows.empty and not eq_rows.empty:
                    ni = ni_rows.sort_values("filed").iloc[-1]["val"]
                    eq = eq_rows.sort_values("filed").iloc[-1]["val"]
                    if eq and abs(eq) > 1e-6 and ni is not None:
                        roe = float(ni) / float(eq)
            if roe is not None:
                recs.append(dict(t=t, sym=sym, roe=roe))
    return pd.DataFrame(recs)

def main():
    print("Loading PIT facts...")
    facts = load_facts()
    print(f"  {len(facts)} facts, {facts['sym'].nunique()} stocks, "
          f"{facts['filed'].min().date()}..{facts['filed'].max().date()}")
    # Build monthly grid from 2010-02 to 2026-08 (PIT XBRL coverage)
    month_ends = pd.date_range("2010-02-28", "2026-08-31", freq="ME")
    print(f"Building PIT ROE panel over {len(month_ends)} month-ends...")
    panel = pit_metric_panel(facts, month_ends)
    print(f"  proxy panels: {panel.shape}, stocks {panel['sym'].nunique()}")
    # Load prices for forward returns (twelve_big, monthly close)
    closes = {}
    for f in glob.glob(f"{PRICE}/*.csv"):
        sym = os.path.basename(f)[:-4]
        try:
            df = pd.read_csv(f, index_col=0, parse_dates=True)[["close"]]
            closes[sym] = df["close"]
        except Exception:
            continue
    price = pd.DataFrame(closes).sort_index()
    p_m = price.resample("ME").last()
    # monthly returns: ret of month m = p_m[m] / p_m[m-1] - 1 ; signal at m-1, earn at m
    ret_m = p_m.pct_change()
    # pivot ROE panel into a matrix (month x stock)
    roe_piv = panel.pivot_table(index="t", columns="sym", values="roe")
    roe_piv = roe_piv.reindex(month_ends).ffill()
    # align returns: signal known at end of month m-1 -> return earned in month m (T+1)
    ret_m = ret_m.reindex(month_ends)
    # rank cross-sectionally
    ranked = roe_piv.rank(axis=1, pct=True)
    # long top quintile, short bottom quintile, equal weight within leg, next-month return
    sleeve = []
    for i in range(1, len(month_ends)):
        sig_t = month_ends[i-1]; earn_t = month_ends[i]
        if sig_t not in ranked.index or earn_t not in ret_m.index:
            continue
        q = ranked.loc[sig_t]
        r = ret_m.loc[earn_t]
        q = q[q.notna()]; r = r[r.notna()]
        common = q.index.intersection(r.index)
        if len(common) < 30:
            continue
        qc = q[common]; rc = r[common]
        top = rc[qc >= 0.8].mean(); bot = rc[qc <= 0.2].mean()
        if pd.notna(top) and pd.notna(bot):
            sleeve.append((earn_t, top - bot))
    sr = pd.DataFrame(sleeve, columns=["date", "ret"]).set_index("date")
    # Optionally forward-fill / aggregate to daily by repeating the month's carry on its days
    print(f"\nMonthly PIT quality LS sleeve: {len(sr)} months")
    print(sr["ret"].describe())
    ann = sr["ret"].mean()*12; sr_m = sr["ret"].mean()/sr["ret"].std()*np.sqrt(12) if sr["ret"].std()>0 else 0
    print(f"  ann {ann*100:.2f}%  SR(m) {sr_m:.3f}")
    # Save monthly version
    sr.to_csv(OUT.replace("_daily", "_monthly"))
    # Daily version: distribute each month's carry proportionally across its tradeable days (rough)
    daily = []
    pm_days = p_m.index
    for i in range(1, len(month_ends)):
        carry = sr.loc[month_ends[i], "ret"] if month_ends[i] in sr.index else None
        if carry is None: continue
        d0 = month_ends[i-1] + pd.Timedelta(days=1)
        d1 = month_ends[i]
        days = pd.date_range(d0, d1, freq="B")
        if len(days) == 0: continue
        each = carry / len(days)
        for dd in days:
            daily.append((dd, each))
    dr = pd.DataFrame(daily, columns=["date","ret"]).set_index("date")
    dr = dr[~dr.index.duplicated()]
    dr.to_csv(OUT)
    print(f"  daily rows {len(dr)}  {dr.index.min().date()}..{dr.index.max().date()}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
