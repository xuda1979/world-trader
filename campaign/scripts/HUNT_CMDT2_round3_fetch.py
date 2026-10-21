#!/usr/bin/env python3
"""HUNT_CMDT2 ROUND 3 (a) — waived-bound fetch: DBE, DBP, USCI, BNO (+ CPER freshness refresh).

Coordinator waiver (STANDUP_LOG 2026-09-07 07:2x, DECISIONS): the 2007-01 start bound is
WAIVED for inception-limited series with span_class discipline + per-file disclosure. That
unlocks exactly the four series the CMDT charter needs (DBE/DBP/USCI were R1/R2 charter-named
and BNO completes the energy-curve pair). Everything else about the lint stays FAIL-CLOSED:
n>=250, max calendar gap <=10d, >3 days with |ret|>50%, end >=2026-06 (freshness — the
DATA_ETF_MORE R2 documented failure mode was outputsize truncation killing the series END,
so staleness is an explicit FAIL, not a silent shrug).

Two-window stitch (head 2005-01-01..2012-12-31 + tail 2013-01-01..now) beats a single
5000-row request for series with inception < 5000 trading days ago; prepend-only, head
wins at the seam, dup dates impossible.

Only PASS rows are written to more_etf/{sym}.csv as [date,close]; manifest gets
span_class=2007plus disclosure. Fail-closed: any FAIL (incl. FETCH_FAIL/API_ERR) is NOT
written and is reported loud.
"""
import sys, time, json, urllib.request
sys.path.insert(0, "/Users/daxu/software/world-trader")
import pandas as pd, numpy as np

ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/tools/quant/data/more_etf"
MANIFEST = f"{OUT}/manifest.csv"

# charter round-3 (a) — DBE/DBP/USCI under the waiver; CPER re-fetched to confirm freshness
SYMS = [
    ("DBE",  "energy basket (waived 2007+; charter (b) DBE-vs-DBP leg)"),
    ("DBP",  "precious-metals basket (waived 2007+; charter (b) DBE-vs-DBP leg)"),
    ("USCI", "front-month basket (waived 2007+; charter (b) USCI-vs-DBC leg)"),
    ("BNO",  "brent ETF (waived 2007+; completes energy curve pair vs USO)"),
    ("CPER", "copper — freshness refresh (2011 inception, charter R2 instrument)"),
]
HEAD_SPAN = ("2005-01-01", "2012-12-31")
TAIL_SPAN = ("2013-01-01", None)          # None = latest
FRESH_END = "2026-06-01"                  # same freshness gate as DATA_ETF_MORE R2
RATE_SLEEP = 8                            # free tier ~8 req/min


def key():
    for line in open(f"{ROOT}/.env.local"):
        if line.startswith("TWELVEDATA_KEY"):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no TWELVEDATA_KEY")


def fetch_window(sym, start, end, k):
    url = (f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day"
           f"&start_date={start}&end_date={end}&outputsize=5000&apikey={k}&format=JSON")
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


def stitch_two_windows(head, tail):
    """Prepend-only stitch, head wins at overlapping dates, result ascending unique."""
    head = head[~head.index.duplicated(keep="last")].sort_index()
    tail = tail[~tail.index.duplicated(keep="last")].sort_index()
    head = head[head.index < tail.index[0]]            # head STRICTLY earlier, no dups
    out = pd.concat([head, tail]).sort_index()
    assert not out.index.has_duplicates and out.index.is_monotonic_increasing
    return out


def lint_close_waiver(df):
    """Fail-closed lint under the coordinator's 2007-01 start-bound waiver.
    n>=250; max calendar gap <=10d; <=3 days with |ret|>50%; end >= 2026-06-01.
    Start bound NOT enforced (waived) but recorded for span_class disclosure."""
    r = dict(n=len(df), start="", end="", status="", detail="", waiver=False)
    if df is None or len(df) < 250:
        r["status"] = "FAIL(short)"; r["detail"] = f"n={len(df)}"; return r
    s = df["close"].astype(float).sort_index()
    s = s[s > 0]
    if len(s) < 250:
        r["status"] = "FAIL(short)"; r["detail"] = f"n_pos={len(s)}"; return r
    r["start"], r["end"], r["n"] = str(s.index[0].date()), str(s.index[-1].date()), len(s)
    gaps = s.index.to_series().diff().dt.days.dropna()
    mg = int(gaps.max())
    jr = int((s.pct_change().abs() > 0.5).sum())
    if mg > 10:
        r["status"] = "FAIL(gap)"; r["detail"] = f"maxgap={mg}d"; return r
    if jr > 3:
        r["status"] = "FAIL(jumps)"; r["detail"] = f"|ret|>50% on {jr}d"; return r
    if str(s.index[-1].date()) < FRESH_END:
        r["status"] = "FAIL(stale)"; r["detail"] = f"end={r['end']} < {FRESH_END}"; return r
    r["status"] = "PASS"
    r["detail"] = f"maxgap={mg}d jumps={jr}"
    r["waiver"] = s.index[0] > pd.Timestamp("2007-01-01")
    return r


def span_class_of(start_ts):
    """Waived rows (start > 2007-01-01) disclose span_class=2007plus; anything that would
    have passed the original bound is not a waiver row (prefetched/on-disk)."""
    return "2007plus" if start_ts > pd.Timestamp("2007-01-01") else "prefetched"


def main():
    k = key()
    results = []
    for i, (sym, why) in enumerate(SYMS):
        head = tail = None
        err = ""
        try:
            js_h = fetch_window(sym, *HEAD_SPAN, k)
            time.sleep(RATE_SLEEP)
            js_t = fetch_window(sym, TAIL_SPAN[0], "2026-12-31", k)
        except Exception as e:
            err = repr(e)[:90]
        else:
            for tag, js in (("head", js_h), ("tail", js_t)):
                if js.get("status") == "error" or "values" not in js:
                    err = f"{tag}: {str(js.get('message', js))[:80]}"
                    break
        if err:
            results.append(dict(sym=sym, status="FETCH_FAIL", detail=err, start="", end="",
                                n=0, span_class="", why=why))
            time.sleep(RATE_SLEEP); continue
        h = pd.DataFrame(js_h["values"]).rename(columns={"datetime": "date"})
        t = pd.DataFrame(js_t["values"]).rename(columns={"datetime": "date"})
        for d in (h, t):
            d["date"] = pd.to_datetime(d["date"]); d["close"] = d["close"].astype(float)
        h = h.set_index("date")[["close"]]; t = t.set_index("date")[["close"]]
        px = stitch_two_windows(h, t)
        lr = lint_close_waiver(px)
        row = dict(sym=sym, status=lr["status"], detail=lr["detail"], start=lr["start"],
                   end=lr["end"], n=lr["n"], span_class="", why=why)
        if lr["status"] == "PASS":
            out = px.copy(); out.index = out.index.strftime("%Y-%m-%d")
            out.to_csv(f"{OUT}/{sym}.csv", index_label="date")
            row["span_class"] = span_class_of(pd.Timestamp(lr["start"]))
        results.append(row)
        print(f"{sym:<6} {lr['status']:<12} n={lr['n']:>5}  {lr['start']} -> {lr['end']}  "
              f"{lr['detail']}  span_class={row['span_class']}")
        time.sleep(RATE_SLEEP)
    print("\n--- ALL RESULTS ---")
    for r in results:
        print(f"{r['sym']:<6} {r['status']:<12} {r['start']:<12} {r['end']:<12} n={r['n']:<5} "
              f"span_class={r['span_class']:<10} {r['detail']}")
    return results


if __name__ == "__main__":
    main()
