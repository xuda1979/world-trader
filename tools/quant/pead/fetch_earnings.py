"""Fetch recent earnings-with-surprise events from Finnhub and match to price panels.

Mirrors tools/wt/catalysts.recent_earnings(). Free-tier Finnhub only exposes the
most recent ~2 weeks of earnings history with populated EPS actuals — a fresh,
real but SHORT window (~600 events across the US market). This is the honest
constraint for a PEAD study with available data.

We store the raw earnings events once, then the backtest joins them to the daily
price panels (twelve_big / twelve_liq) to measure post-earnings drift.
"""
from __future__ import annotations
import sys, os, json, datetime, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repo root (tools/wt)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))        # tools/
from wt import catalysts

def main():
    outdir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(outdir, exist_ok=True)
    recs, err = catalysts.recent_earnings(days_back=30, days_forward=0)
    if err:
        print("ERR", err); return
    with open(os.path.join(outdir, "earnings_events.json"), "w") as f:
        json.dump(recs, f, indent=2)
    print(f"saved {len(recs)} earnings events with surprise")
    # price panels available
    for panel in ["twelve_big", "twelve_liq"]:
        d = os.path.join(outdir, "..", "..", "data", panel)
        names = len(glob.glob(os.path.join(d, "*.csv")))
        # intersection count
        syms = {r["sym"] for r in recs}
        have = {os.path.basename(p)[:-4] for p in glob.glob(os.path.join(d, "*.csv"))}
        inter = syms & have
        print(f"  {panel}: {names} price panels, {len(inter)} have an earnings event in window")

if __name__ == "__main__":
    main()
