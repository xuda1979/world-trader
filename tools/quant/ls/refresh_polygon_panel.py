#!/usr/bin/env python3
"""APPEND-ONLY refresh of the ls polygon panel (tools/quant/data/polygon).

WARNING / history: the previous version of this script rewrote every file
from a single Polygon call with a ~730d window. Polygon free tier caps at
~501 bars/call, so that TRUNCATED the panel 516 -> 500/501 rows and
destroyed the leading 2024-07 history. That incident (RESEARCH_LOG
2026-08-13) made the champion's SR 1.686 unreproducible)Skip

DESIGN RULE (this version): APPEND-ONLY. For each symbol we read the
existing file and fetch ONLY bars newer than its last date (small recent
window -> well under any cap), then append the missing rows. We NEVER
rewrite the historical portion. This preserves full history and only
advances the panel forward. NKE-style transient gaps self-heal on the
next run (they were behind, so their window catches them).

Rate limits (free tier: 5 calls/min) -> ~12s sleep. 85 symbols x 2 calls
(probe + fetch) + retry pass ~ 35-45 min.

Usage: python3 -m tools.quant.ls.refresh_polygon_panel [--dry-run]
"""
from __future__ import annotations
import os, sys, time, json, glob
import urllib.request, urllib.error
import datetime as _dt
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PANEL_DIR = os.path.join(ROOT, "tools", "quant", "data", "polygon")
ENV_PATH = os.path.join(ROOT, ".env.local")
DRY = "--dry-run" in sys.argv

SLEEP_S = 12.0
FETCH_LOOKBACK_DAYS = 45   # oldest->newest: safe to grab a recent window only
RETRY_ROUNDS = 2


def load_key():
    for line in open(ENV_PATH):
        line = line.strip()
        if line and "=" in line:
            k, v = line.split("=", 1)
            if k.strip() == "POLYGON_KEY":
                return v.strip().strip('"').strip("'")
    raise SystemExit("no POLYGON_KEY in .env.local")


def fetch_since(sym, key, since_date):
    """Fetch daily bars for sym in (since_date-5d .. today) -> list of row dicts."""
    end = _dt.date.today().strftime("%Y-%m-%d")
    start = (pd.to_datetime(since_date) - pd.Timedelta(days=5)).strftime("%Y-%m-%d")
    url = (f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/"
           f"{start}/{end}?adjusted=true&sort=asc&limit=5000&apiKey={key}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        return None, "rate-limited" if e.code == 429 else f"HTTP {e.code}"
    except Exception as e:
        return None, str(e)[:120]
    res = d.get("results") or []
    rows = []
    for r in res:
        rows.append({
            "date": _dt.datetime.fromtimestamp(r["t"] / 1000, _dt.timezone.utc).strftime("%Y-%m-%d"),
            "open": r["o"], "high": r["h"], "low": r["l"],
            "close": r["c"], "vol": r.get("v", ""),
        })
    return rows, None


def main() -> int:
    key = load_key()
    paths = sorted(glob.glob(os.path.join(PANEL_DIR, "*.csv")))
    if not paths:
        raise SystemExit(f"no CSVs in {PANEL_DIR}")
    print(f"panel: {len(paths)} symbols in {PANEL_DIR}")
    if DRY:
        print("dry-run — exit")
        return
    ok, changed, fail = set(), 0, {}
    for round_no in range(1, RETRY_ROUNDS + 1):
        todo = [p for p in paths if os.path.basename(p)[:-4] not in ok and
                os.path.basename(p)[:-4] not in fail]
        if not todo:
            break
        print(f"--- pass {round_no}/{RETRY_ROUNDS}: {len(todo)} symbols ---", flush=True)
        for i, pfile in enumerate(todo):
            sym = os.path.basename(pfile)[:-4]
            try:
                cur = pd.read_csv(pfile)
            except Exception as e:
                fail[sym] = f"read: {e}"; print(f"  {sym} READ-FAIL {e}"); continue
            cur["date"] = cur["date"].astype(str)
            cur = cur.sort_values("date").drop_duplicates("date")
            last = cur["date"].iloc[-1]
            rows, err = fetch_since(sym, key, last)
            if rows is None:
                fail[sym] = err
                print(f"[{i+1}/{len(todo)}] {sym} FAIL ({err})", flush=True)
                time.sleep(20 if err == "rate-limited" else SLEEP_S)
                continue
            new = pd.DataFrame(rows).drop_duplicates("date")
            to_add = new[~new["date"].isin(set(cur["date"]))]
            if to_add.empty:
                ok.add(sym)
                print(f"[{i+1}/{len(todo)}] {sym} up-to-date ({len(cur)} rows)", flush=True)
            else:
                merged = pd.concat(
                    [cur, to_add[["date", "open", "high", "low", "close", "vol"]]],
                    ignore_index=True).drop_duplicates("date").sort_values("date")
                if not DRY:
                    merged.to_csv(pfile, index=False)
                ok.add(sym); changed += 1
                print(f"[{i+1}/{len(todo)}] {sym} +{len(to_add)} row(s) "
                      f"({to_add['date'].iloc[0]}..{to_add['date'].iloc[-1]}) "
                      f"-> {len(merged)} rows", flush=True)
            time.sleep(SLEEP_S)
        if fail:
            print(f"--- retry: {sorted(fail)} ---", flush=True)
            time.sleep(30)
    print(f"\nDone: {len(ok)}/{len(paths)} processed, {changed} updated; "
          f"failed: {fail or 'none'}")
    if fail:
        # do NOT leave as committed data; the retry pass already re-attempted
        print("NOTE: failed symbols were NOT updated (kept prior state). Re-run to finish.")

if __name__ == "__main__":
    main()
