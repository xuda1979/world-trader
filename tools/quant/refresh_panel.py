#!/usr/bin/env python3
"""Refresh twelve_big + twelvedata panels (fixes the skip-if-full logic).

The extend/fetch scripts skip symbols already at >=4900 rows, so the
panels can never move past their fetch date. This script ALWAYS
refetches every symbol (outputsize=5000, the rolling 20y window) and
overwrites the file — the API returns the most recent 5000 bars, so the
window shifts forward as new data lands. ~291 names x 9s sleep ≈ 45 min;
TwelveData free tier 800 req/day, 8 req/min — safe.

Usage: python3 tools/quant/refresh_panel.py [--dry-run]
"""
from __future__ import annotations
import os, sys, time, json, urllib.request, glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIRS = [
    os.path.join(ROOT, "tools", "quant", "data", "twelve_big"),
    os.path.join(ROOT, "tools", "quant", "data", "twelve_liq"),
    os.path.join(ROOT, "tools", "quant", "data", "twelvedata"),
]
ENV_PATH = os.path.join(ROOT, ".env.local")
DRY = "--dry-run" in sys.argv

def load_key():
    for line in open(ENV_PATH):
        line = line.strip()
        if line and "=" in line:
            k, v = line.split("=", 1)
            if k.strip() == "TWELVEDATA_KEY":
                return v.strip().strip('"').strip("'")
    raise SystemExit("no TWELVEDATA_KEY")

def fetch(sym, key):
    url = (f"https://api.twelvedata.com/time_series?symbol={sym}"
           f"&interval=1day&outputsize=5000&apikey={key}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except Exception as e:
        return None, str(e)[:120]
    if d.get("status") != "ok":
        return None, d.get("message") or str(d)[:120]
    vals = list(reversed(d.get("values", [])))
    if not vals:
        return None, "no values"
    lines = ["date,open,high,low,close,vol"]
    for v in vals:
        lines.append(",".join([v["datetime"], str(v["open"]), str(v["high"]),
                               str(v["low"]), str(v["close"]), str(v.get("volume",""))]))
    return "\n".join(lines), None

def main():
    key = load_key()
    # do NOT dedup by filename: the same symbol may exist in several dirs
    # (twelve_big/twelve_liq/twelvedata) and EACH copy must be refreshed
    import datetime as _dt
    paths = []
    for d in DATA_DIRS:
        for f in sorted(glob.glob(os.path.join(d, "*.csv"))):
            paths.append(f)
    # symbols that will never resolve on TwelveData (underscore FX naming,
    # FRED-only indices) — skip them so routine runs stay silent
    SKIP_SYMS = {"EUR_JPY", "USD_JPY", "VIXCLS"}
    # skip files already refreshed today (mtime today = provider-current;
    # some symbols' API data legitimately ends earlier — e.g. SQ renamed
    # to XYZ — and must not be refetched every run)
    todo = []
    for p in paths:
        if os.path.basename(p).replace(".csv", "") in SKIP_SYMS:
            continue
        mt = _dt.date.fromtimestamp(os.path.getmtime(p))
        if mt != _dt.date.today():
            todo.append(p)
    paths = todo
    print(f"refreshing {len(paths)} files (dry={DRY})", flush=True)
    ok = err = skip = 0
    for i, path in enumerate(paths):
        sym = os.path.basename(path).replace(".csv", "")
        if DRY:
            print(f"[{i+1}/{len(paths)}] would fetch {sym} -> {path}"); continue
        content, msg = fetch(sym, key)
        if content is None:
            err += 1
            print(f"[{i+1}/{len(paths)}] {sym}: ERR {msg}", flush=True)
        else:
            rows = len(content.splitlines()) - 1
            with open(path, "w") as fh:
                fh.write(content + "\n")
            last = content.splitlines()[-1].split(",")[0]
            ok += 1
            print(f"[{i+1}/{len(paths)}] {sym} ({path.split('/')[-2]}): {rows} rows, last {last}", flush=True)
        time.sleep(9)
    print(f"DONE: {ok} ok, {err} err, {skip} skip")

if __name__ == "__main__":
    main()
