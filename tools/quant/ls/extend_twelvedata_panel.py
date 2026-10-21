#!/usr/bin/env python3
"""Extend the champion's home panel (tools/quant/data/twelvedata) to full
~20y history (5000 bars/symbol) via the TwelveData free tier.

The 90-name panel currently holds ~2000 bars (8y).  For a LONGER, more
reliable test of the validated champion universe, refetch each symbol with
outputsize=5000 (~20y).  Skips symbols already at >=4900 rows; overwrites
shorter files.  ~90 symbols x ~9s sleep = ~15 min.

Usage:
  python -m tools.quant.ls.extend_twelvedata_panel
"""
from __future__ import annotations
import os, sys, time, json, urllib.request, glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DATA_DIR = os.path.join(ROOT, "tools", "quant", "data", "twelvedata")
ENV_PATH = os.path.join(ROOT, ".env.local")
MIN_ROWS = 4900  # skip if already >= this many rows


def _load_key() -> str:
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == "TWELVEDATA_KEY":
                return v.strip().strip('"').strip("'")
    raise SystemExit("no TWELVEDATA_KEY in .env.local")


def fetch(sym: str, key: str):
    url = (f"https://api.twelvedata.com/time_series?symbol={sym}"
           f"&interval=1day&outputsize=5000&apikey={key}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    d = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if d.get("status") != "ok":
        return None, d.get("message") or str(d)[:120]
    vals = list(reversed(d.get("values", [])))
    if not vals:
        return None, "no values"
    lines = ["date,open,high,low,close,vol"]
    for v in vals:
        lines.append(",".join([v["datetime"], str(v["open"]), str(v["high"]),
                               str(v["low"]), str(v["close"]), str(v["volume"])]))
    return "\n".join(lines) + "\n", None


def main() -> int:
    key = _load_key()
    syms = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(DATA_DIR, "*.csv")))
    print(f"{len(syms)} symbols in {DATA_DIR}", flush=True)
    done = skip = fail = 0
    for i, sym in enumerate(syms):
        path = os.path.join(DATA_DIR, f"{sym}.csv")
        rows = sum(1 for _ in open(path)) - 1
        if rows >= MIN_ROWS:
            skip += 1
            print(f"[{i+1}/{len(syms)}] {sym}: skip ({rows} rows)", flush=True)
            continue
        try:
            content, err = fetch(sym, key)
            if content is None:
                print(f"[{i+1}/{len(syms)}] {sym}: FAIL {err}", flush=True)
                fail += 1
            else:
                with open(path, "w") as f:
                    f.write(content)
                done += 1
                n = len(content.splitlines()) - 1
                print(f"[{i+1}/{len(syms)}] {sym}: ok ({rows}->{n} rows)", flush=True)
        except Exception as e:
            print(f"[{i+1}/{len(syms)}] {sym}: EXC {type(e).__name__} {e}", flush=True)
            fail += 1
        time.sleep(9)
    print(f"DONE done={done} skip={skip} fail={fail}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
