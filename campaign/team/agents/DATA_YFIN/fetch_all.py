"""DATA_YFIN batch fetch runner: /tmp/yfin_plan.json -> yfin/*.csv + manifests.

Rate-limit aware: long sleep between tickers, exponential backoff on failures
(Yahoo 403/YFRateLimitError observed on this IP). Resumable; skip already-done.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import yfin_dl  # noqa: E402

PLAN = "/tmp/yfin_plan.json"
SLEEP = 8.0          # base sleep between tickers (charter: rate-limit-sleep)
BACKOFF = 60.0       # extra sleep on rate-limit errors
MAX_TRIES = 4


def fetch_one(sym):
    """Fetch+write one symbol; returns 'ok' | 'empty' | 'rl' (rate-limited)."""
    try:
        rows = yfin_dl.fetch_yf(sym)
    except Exception as e:
        msg = str(e)
        return "rl" if ("Rate" in msg or "429" in msg or "403" in msg) else "empty"
    if not rows or len(rows) < 250:
        return "empty"
    yfin_dl.write_csv(sym, rows)
    return "ok"


def main():
    plan = json.load(open(PLAN))
    syms = [s for grp in ("equity", "etf", "fx") for s in plan[grp]]
    done, empty, rl = [], [], []
    for i, sym in enumerate(syms):
        out = os.path.join(yfin_dl.OUT, f"{sym}.csv")
        if os.path.isfile(out):
            done.append(sym)
            continue
        status = "rl"
        for attempt in range(MAX_TRIES):
            status = fetch_one(sym)
            if status != "rl":
                break
            time.sleep(BACKOFF * (attempt + 1))
        (done if status == "ok" else rl if status == "rl" else empty).append(sym)
        print(f"[{i+1}/{len(syms)}] {sym}: {status}", flush=True)
        time.sleep(SLEEP)
    print(f"DONE ok={len(done)} empty={len(empty)} rl={len(rl)}")
    if rl:
        print("RATE_LIMITED:", ",".join(rl))


if __name__ == "__main__":
    main()
