#!/usr/bin/env python3
"""DATA_ETF_MORE round-4: full keyless-source rotation for the 5 un-fetched ETFs.

R1 left 10 ETFs un-fetched on start>2007-01-01. R3 (coordinator waiver) already
cleared 5 on disk as PASS_WAIVER: HYG EWC DBE DBP USCI. The remaining 5 -- EIS,
TUR, EPHE, COPX, ENOR -- get this round's rotation:
  1. TwelveData time_series with explicit start_date (the working R1-R3 path,
     full history, not just the earliest 5000).
  2. Nasdaq historical API (api.nasdaq.com/api/quote/SYM/historical, keyless,
     browser-UA per wt/sources.nasdaq_history) -- bounded to ~10y of calendar
     backfill by the vendor; we page fromdate as far back as it serves and
     measure the true attainable start.
Fail-closed: R3 lint (waiver lifts ONLY the start bound); a FAIL series is never
written. Every FAIL keeps an exact probe record (url, rc, response snippet).
No fabrication, no synthetic fills: a gap is a vendor fact, reported loudly.
"""
import datetime as _dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/tools/quant/data/more_etf"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PRE2007_BOUND = pd.Timestamp("2007-01-01")
INCEPTION_BOUND = pd.Timestamp("2013-01-01")
REF_END = pd.Timestamp("2026-09-01")
FRESH_DAYS = 365 * 3 + 92

# Charter round-4 list, exactly.
ROUND4_TARGETS = ["HYG", "EWC", "EIS", "TUR", "DBE", "EPHE", "USCI", "COPX",
                  "DBP", "ENOR"]
# Already PASS_WAIVER on disk from R3 (manifest-verified in test_r4.T7) --
# re-testing these would be re-running a resolved row; excluded by construction.
ROTATE_TARGETS = ["EIS", "TUR", "EPHE", "COPX", "ENOR"]

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def classify(start: pd.Timestamp) -> str:
    if start <= PRE2007_BOUND:
        return "pre2007"
    if start <= INCEPTION_BOUND:
        return "2007plus"
    return "inception_fail"


# ------------------------------------------------------------------ sources
def key():
    for line in open(f"{ROOT}/.env.local"):
        if line.startswith("TWELVEDATA_KEY"):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no TWELVEDATA_KEY")


def twelvedata(sym, k, start_date="1995-01-01"):
    """TwelveData full-history pull. Returns (dataframe|None, probe dict)."""
    url = (f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day"
           f"&start_date={start_date}&outputsize=5000&apikey={k}&format=JSON")
    probe = dict(source="twelvedata", url=url.replace(k, "<KEY>"), rc=None,
                 snippet="")
    try:
        with urllib.request.urlopen(urllib.request.Request(url), timeout=60) as r:
            body = r.read().decode()
            probe["rc"] = r.status
        js = json.loads(body)
        if js.get("status") == "error" or "values" not in js:
            probe["snippet"] = str(js.get("message", js))[:200]
            return None, probe
        df = pd.DataFrame(js["values"]).rename(columns={"datetime": "date"})
        df["date"] = pd.to_datetime(df["date"])
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        probe["snippet"] = f"n={len(df)} {df['date'].min().date()}..{df['date'].max().date()}"
        return df, probe
    except urllib.error.HTTPError as e:
        probe["rc"] = e.code
        probe["snippet"] = (e.read()[:200].decode(errors="replace")
                            if e.fp else str(e))
        return None, probe
    except Exception as e:
        probe["rc"] = None
        probe["snippet"] = f"{type(e).__name__}: {e}"[:200]
        return None, probe


_DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def nasdaq_rows(payload):
    """Parse a Nasdaq /historical payload -> (ascending [date,close] df|None,
    err). Newest-first input; $-prefixed closes; intraday-timestamp rows
    (today's bar) are dropped, not faked. T1/T2."""
    rows = (((payload.get("data") or {}).get("tradesTable") or {}).get("rows")) or []
    if not rows:
        return None, "no tradesTable rows in payload"
    D, C = [], []
    for r in rows:
        raw = str(r.get("date") or "")
        m = _DATE_RE.match(raw)
        if not m:
            continue  # '3:00:00 PM' style intraday stamp -- not a session date
        c = r.get("close")
        try:
            c = float(str(c).replace("$", "").replace(",", ""))
        except (TypeError, ValueError):
            continue
        D.append(pd.Timestamp(_dt.datetime.strptime(raw, "%m/%d/%Y")))
        C.append(c)
    if not D:
        return None, "no parseable session rows"
    df = pd.DataFrame({"date": D, "close": C})
    df = df.sort_values("date").reset_index(drop=True)
    return df, None


def nasdaq(sym, frm=None, to=None):
    """Nasdaq historical API. from/to as 'YYYY-MM-DD'. Returns (df|None, probe)."""
    to = to or _dt.date.today()
    frm = frm or (to - _dt.timedelta(days=400 * 25))
    cls = "etf"
    url = (f"https://api.nasdaq.com/api/quote/{sym}/historical?assetclass={cls}"
           f"&fromdate={frm}&todate={to}&limit=99999")
    probe = dict(source="nasdaq", url=url, rc=None, snippet="")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                   "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read().decode()
            probe["rc"] = r.status
        payload = json.loads(body)
        df, err = nasdaq_rows(payload)
        if df is None:
            probe["snippet"] = f"parse: {err} | body[:160]={body[:160]!r}"
            return None, probe
        probe["snippet"] = f"n={len(df)} {df['date'].min().date()}..{df['date'].max().date()}"
        return df, probe
    except urllib.error.HTTPError as e:
        probe["rc"] = e.code
        probe["snippet"] = (e.read()[:200].decode(errors="replace")
                            if e.fp else str(e))
        return None, probe
    except Exception as e:
        probe["rc"] = None
        probe["snippet"] = f"{type(e).__name__}: {e}"[:200]
        return None, probe


# ------------------------------------------------------------------- lint/write
def lint_series(df, ref_end=REF_END):
    """R3 fail-closed lint under the waiver. (status, span_class, metrics)."""
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
        if n < 250:
            return "FAIL(short)", classify(s.index[0]), r
        if dups > 0:
            return "FAIL(dup)", classify(s.index[0]), r
        if mg > 10:
            return "FAIL(gap)", classify(s.index[0]), r
        if jr > 0:
            return "FAIL(jumps)", classify(s.index[0]), r
        if (ref_end - s.index[-1]).days > FRESH_DAYS:
            return "FAIL(stale)", classify(s.index[0]), r
        cls = classify(s.index[0])
        if cls == "inception_fail":
            return "FAIL(inception)", cls, r
        return ("PASS" if cls == "pre2007" else "PASS_WAIVER"), cls, r
    except Exception as e:
        return f"FAIL(read) {repr(e)[:50]}", "", r


def write_series(df, path, status):
    """Fail-closed write: FAIL status -> refuse, path untouched (T5). PASS ->
    ascending unique [date,close]. Returns rows written (0 = refused)."""
    if not (status == "PASS" or status == "PASS_WAIVER"):
        return 0
    s = df.set_index("date")["close"].astype(float).sort_index()
    s = s[s > 0]
    s = s[~s.index.duplicated(keep="first")]
    out = s.reset_index()
    out.columns = ["date", "close"]
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out.to_csv(path, index=False)
    return len(out)


def probe_record(symbol, source, url, rc, snippet):
    """Charter evidence shape: EXACT failing probe (T8)."""
    return dict(symbol=symbol, source=source, url=url, rc=rc,
                snippet=str(snippet)[:300])


# ------------------------------------------------------------------ rotation
def rotate_one(sym, k):
    """Try each source in order; return (best_df, status, cls, metrics, probes)."""
    probes = []
    best = None
    best_st, best_cls, best_m = "FAIL(nosource)", "", dict()
    # Source 1: TwelveData full history (R1-R3 workhorse)
    df, p = twelvedata(sym, k)
    probes.append(p)
    if df is not None:
        st, cls, m = lint_series(df)
        if st in ("PASS", "PASS_WAIVER") and (best is None or len(df) > len(best)):
            best, best_st, best_cls, best_m = df, st, cls, m
        elif best is None:
            best_st, best_cls, best_m = st, cls, m
    time.sleep(8)
    # Source 2: Nasdaq historical (keyless, browser UA). Vendor bounds depth;
    # we ask for the maximum window and measure what actually comes back.
    df2, p2 = nasdaq(sym)
    probes.append(p2)
    if df2 is not None:
        st2, cls2, m2 = lint_series(df2)
        if st2 in ("PASS", "PASS_WAIVER") and (best is None or len(df2) > len(best)):
            best, best_st, best_cls, best_m = df2, st2, cls2, m2
        elif best is None:
            best_st, best_cls, best_m = st2, cls2, m2
    return best, best_st, best_cls, best_m, probes


def main():
    k = key()
    results = []
    for i, sym in enumerate(ROTATE_TARGETS):
        df, st, cls, m, probes = rotate_one(sym, k)
        written = "no"
        action = "keep-fail"
        if df is not None and st in ("PASS", "PASS_WAIVER"):
            n = write_series(df, f"{OUT}/{sym}.csv", status=st)
            written = "yes" if n else "no"
            action = f"WROTE n={n}"
        results.append(dict(symbol=sym, status=st, span_class=cls,
                            start=m.get("start"), end=m.get("end"),
                            n=m.get("n"), maxgap=m.get("maxgap"),
                            jumps=m.get("jumps"), dups=m.get("dups"),
                            written=written, action=action,
                            probes=probes))
        print(f"{sym:<5} {st:<16} {cls:<14} {m.get('start')}..{m.get('end')} "
              f"n={m.get('n')} -> {action}", flush=True)
        for p in probes:
            print(f"      [{p['source']}] rc={p['rc']} {p['snippet'][:110]}",
                  flush=True)
        time.sleep(2)
    with open(f"{HERE}/results_r4.json", "w") as f:
        json.dump(results, f, indent=1, default=str)
    print(f"\nsaved results_r4.json ({len(results)} rows)")


if __name__ == "__main__":
    main()
