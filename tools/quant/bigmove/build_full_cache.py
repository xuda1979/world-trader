"""Incremental parser cache for the FULL EDGAR corpus (edgar_facts_full/).

parse_facts() on a raw companyfacts JSON takes ~1-2s per file (it builds
per-tag DataFrames over the full XBRL history) — re-parsing the whole corpus
every screen run becomes minutes, then hours as the fetch fills ~8k files.
This caches ONLY the latest-filed value of the NCAV-relevant tags per ticker
once per file; buffett_full_screen.py then reads the tiny cache.

Output: data/full_cache.json  {ticker: {tag: [val, filed_iso], ...}}
Manifest of parsed files in data/full_cache_done.json (resume-friendly).
"""
from __future__ import annotations
import os, sys, json, glob
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.chdir(HERE)
from edgar_fundamentals import parse_facts

FULL = os.path.join(HERE, "data", "edgar_facts_full")
CACHE = os.path.join(HERE, "data", "full_cache.json")
DONE = os.path.join(HERE, "data", "full_cache_done.json")
NEED = ["book_equity", "assets", "cur_assets", "cur_liab", "shares", "cash", "net_income"]
CACHE_VERSION = 2  # bump to force a full rebuild

def main():
    files = sorted(glob.glob(os.path.join(FULL, "*.json")))
    cache = {}
    done = set()
    if os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE))
        except Exception:
            pass
    if os.path.exists(DONE):
        try:
            meta = json.load(open(DONE))
            done = set(meta["files"]) if isinstance(meta, dict) else set(meta)
            if isinstance(meta, dict) and meta.get("version") != CACHE_VERSION:
                print(f"cache version mismatch: full rebuild ({len(cache)} entries)")
                cache, done = {}, set()
        except Exception:
            pass
    n_new = 0
    for fp in files:
        t = os.path.basename(fp)[:-5]
        if t in done:
            continue
        facts = parse_facts(fp)
        rec = {}
        if facts:
            # PERIOD-ALIGNED NCAV triple: latest period with all three of
            # cur_assets/assets/book_equity (else latest-filed per tag).
            d3 = {k: facts.get(k) for k in ("cur_assets", "assets", "book_equity")}
            if all(d is not None and len(d) for d in d3.values()):
                m = d3["cur_assets"][["period", "filed", "val"]].merge(
                    d3["assets"][["period", "filed", "val"]], on="period", suffixes=("_ca", "_a")
                ).merge(
                    d3["book_equity"][["period", "filed", "val"]], on="period"
                )
                m["filed"] = pd.to_datetime(m[["filed_ca", "filed_a", "filed"]].max(axis=1))
                m = m.sort_values(["period", "filed"])
                if len(m):
                    last = m.iloc[-1]
                    rec["cur_assets"] = [float(last["val_ca"]), str(last["filed_ca"].date())]
                    rec["assets"] = [float(last["val_a"]), str(last["filed_a"].date())]
                    rec["book_equity"] = [float(last["val"]), str(last["filed"].date())]
                    rec["ncav_period"] = str(last["period"].date())
                else:
                    for k in ("cur_assets", "assets", "book_equity"):
                        d = d3[k].sort_values(["filed", "period"]).iloc[-1]
                        rec[k] = [float(d["val"]), str(d["filed"].date())]
            else:
                for k in ("cur_assets", "assets", "book_equity"):
                    d = d3.get(k)
                    if d is not None and len(d):
                        last = d.sort_values(["filed", "period"]).iloc[-1]
                        rec[k] = [float(last["val"]), str(last["filed"].date())]
            for k in ("cur_liab", "shares", "cash", "net_income"):
                d = facts.get(k)
                if d is not None and len(d):
                    last = d.sort_values(["filed", "period"]).iloc[-1]
                    rec[k] = [float(last["val"]), str(last["filed"].date())]
        cache[t] = rec
        done.add(t)
        n_new += 1
        if n_new % 100 == 0:
            print(f"  parsed {n_new} new (total {len(done)})", flush=True)
    json.dump(cache, open(CACHE, "w"))
    json.dump({"version": CACHE_VERSION, "files": sorted(done)}, open(DONE, "w"))
    print(f"cache: {len(cache)} tickers ({n_new} new), written {CACHE}")

if __name__ == "__main__":
    main()
