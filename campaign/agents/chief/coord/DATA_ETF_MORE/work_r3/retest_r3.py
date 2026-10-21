#!/usr/bin/env python3
"""DATA_ETF_MORE round-3: coordinator start-bound WAIVER re-test (charter 3a).

Round 2 established these 20 series fail the R1/R2 start gate (start>2007-01-01).
The coordinator waived the 2007-01 bound for inception-limited series: the series
is admitted with span_class disclosed per-file so downstream hunts filter on it.

Classing (charter 3a):
  pre2007        start <= 2007-01-01          -> status PASS (normal hunt universe)
  2007plus       2007-01-01 < start <= 2013-01-01 -> PASS_WAIVER, written, flagged
  inception_fail start >  2013-01-01         -> FAIL(inception), NOT written as a
                 huntable series (no hunt-usable depth; loud in manifest)

Fail-closed: the waiver lifts ONLY the start bound. Every other R2 gate still
fires: n>=250, max calendar gap<=10d, |ret|>50% on <=3d, dup dates, and
freshness (end within ~3y of the run's reference end, so a fetched-then-truncated
or dead series can't masquerade as current — the R2 truncation bug's gate).
"""
import json
import os
import time
import urllib.request

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/tools/quant/data/more_etf"
HERE = os.path.dirname(os.path.abspath(__file__))

PRE2007_BOUND = pd.Timestamp("2007-01-01")
INCEPTION_BOUND = pd.Timestamp("2013-01-01")
REF_END = pd.Timestamp("2026-09-01")   # freshness reference (run date 2026-09-07)
FRESH_DAYS = 365 * 3 + 92              # end must be within ~3.25y of REF_END

# Charter 3(a) re-test list, exactly the 20 named rows.
SYMS = [
    "HYG", "JNK", "EMB", "BND", "UUP", "EWC", "EEM", "DBC", "GSG", "DBA",
    "UNG", "CANE", "CORN", "SOYB", "WEAT", "CPER", "DBP", "DBE", "BNO", "USCI",
]


def classify(start: pd.Timestamp) -> str:
    """Charter 3(a) span class from a series' first date."""
    if start <= PRE2007_BOUND:
        return "pre2007"
    if start <= INCEPTION_BOUND:
        return "2007plus"
    return "inception_fail"


def key():
    for line in open(f"{ROOT}/.env.local"):
        if line.startswith("TWELVEDATA_KEY"):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no TWELVEDATA_KEY")


def fetch_one(sym, k, start_date="1995-01-01"):
    """Full-history pull: start+outputsize to dodge the R2 5000-row-end-truncation
    bug; capped outputsize keeps the free tier honest (verified: max series 7.7k rows)."""
    url = (f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day"
           f"&start_date={start_date}&outputsize=5000&apikey={k}&format=JSON")
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


def lint_series(df, ref_end=REF_END):
    """Fail-closed lint under the waiver. Returns (status, span_class, metrics).

    df: DataFrame[date (datetime64), close (numeric)] any order.
    Waiver lifts ONLY the start bound; all other gates fire identically.
    """
    r = dict(n=len(df), start="", end="", maxgap="", zrun="", jumps="", dups="")
    try:
        s = df.set_index("date")["close"].astype(float).sort_index()
        s = s[s > 0]
        n = len(s)
        r.update(n=n, start=str(s.index[0].date()), end=str(s.index[-1].date()))
        dups = int(s.index.duplicated().sum())
        gaps = s.index.to_series().diff().dt.days.dropna()
        mg = int(gaps.max())
        jr = int((s.pct_change().abs() > 0.5).sum())
        zrun = int((s.diff() == 0).groupby((s.diff() != 0).cumsum()).cumsum().max())
        r.update(maxgap=mg, zrun=zrun, jumps=jr, dups=dups)

        # --- R1/R2 gates, unchanged (waiver does NOT touch these) ---
        if n < 250:
            return "FAIL(short)", classify(s.index[0]), r
        if dups > 0:
            return "FAIL(dup)", classify(s.index[0]), r
        if mg > 10:
            return "FAIL(gap)", classify(s.index[0]), r
        # jump gate TIGHTENED vs R2's jr>3 -> any >50% 1d move fails. Verified
        # pre-implementation: all 70 real R2 series measure jumps=0, so this
        # pins the pre-written test (T5) without reclassifying any real series.
        if jr > 0:
            return "FAIL(jumps)", classify(s.index[0]), r
        age_days = (ref_end - s.index[-1]).days
        if age_days > FRESH_DAYS:
            return "FAIL(stale)", classify(s.index[0]), r

        # --- the ONE gate the waiver lifts ---
        cls = classify(s.index[0])
        if cls == "inception_fail":
            return "FAIL(inception)", cls, r
        return ("PASS" if cls == "pre2007" else "PASS_WAIVER"), cls, r
    except Exception as e:
        return f"FAIL(read) {repr(e)[:50]}", "", r


def write_series(df, path):
    """Ascending, unique-date [date,close] write (T6)."""
    s = df.set_index("date")["close"].astype(float).sort_index()
    s = s[s > 0]
    s = s[~s.index.duplicated(keep="first")]
    out = s.reset_index()
    out.columns = ["date", "close"]
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out.to_csv(path, index=False)
    return len(out)


def main():
    k = key()
    results = []
    for i, sym in enumerate(SYMS):
        on_disk = os.path.exists(f"{OUT}/{sym}.csv")
        try:
            js = fetch_one(sym, k)
            if js.get("status") == "error" or "values" not in js:
                results.append(dict(symbol=sym, status="API_ERR",
                                    detail=str(js.get("message", js))[:90],
                                    span_class="", written="no",
                                    action="keep-fail"))
                print(f"{sym:<6} API_ERR {str(js.get('message', js))[:70]}", flush=True)
            else:
                df = pd.DataFrame(js["values"]).rename(columns={"datetime": "date"})
                df["date"] = pd.to_datetime(df["date"])
                st, cls, m = lint_series(df)
                action, written = "keep-fail", "no"
                if st in ("PASS", "PASS_WAIVER"):
                    write_series(df, f"{OUT}/{sym}.csv")
                    action = "WROTE" + (" (re-verified fresh full history)" if on_disk else " (new)")
                    written = "yes"
                elif on_disk:
                    action = "KEPT-FAIL-ROW (on-disk file left; flagged loud)"
                results.append(dict(symbol=sym, status=st, span_class=cls,
                                    start=m["start"], end=m["end"], n=m["n"],
                                    maxgap=m["maxgap"], jumps=m["jumps"],
                                    dups=m["dups"], written=written,
                                    action=action))
                print(f"{sym:<6} {st:<16} {cls:<14} {m['start']}..{m['end']} "
                      f"n={m['n']:<5} gap={m['maxgap']}d jumps={m['jumps']} -> {action}",
                      flush=True)
        except Exception as e:
            results.append(dict(symbol=sym, status="FETCH_FAIL",
                                detail=repr(e)[:90], span_class="", written="no",
                                action="keep-fail"))
            print(f"{sym:<6} FETCH_FAIL {repr(e)[:70]}", flush=True)
        if (i + 1) % 8 == 0:
            print("   ... rate-limit sleep 62s (8 req/min) ...", flush=True)
            time.sleep(62)
        else:
            time.sleep(8)

    import json as _json
    with open(f"{HERE}/results_retest_r3.json", "w") as f:
        _json.dump(results, f, indent=1, default=str)
    print(f"\nsaved results_retest_r3.json ({len(results)} rows)")


if __name__ == "__main__":
    main()
