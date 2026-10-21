#!/usr/bin/env python3
"""DATA_ETF_MORE round-2 final: last must-fetches + charter-(b) paging retries.

Fix vs work_r2/complete_r2.py: start_date=1995 + outputsize=5000 alone returns the
EARLIEST 5000 rows and silently truncates the series end (~2015) -> would pass the
start-lint while writing a dead series. Here we page two explicit windows
(A: 1995-01-01..2012-12-31, B: 2013-01-01..today), stitch, and add a freshness gate
(end >= 2026-06-01) so a stale/truncated series fails closed.

Contract (as R1/R2): TwelveData free tier 8 req/min; fail-closed lint
start<=2007-01-01, n>=250, max gap<=10 cal days, |ret|>50% on <=3 days.
PASS -> more_etf/{id}.csv [date,close] ascending. FAILs are documented, not written.
Results -> work_r2/results_final.json for FINDINGS.md.
"""
import json, time, urllib.request
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/tools/quant/data/more_etf"
FRESH = pd.Timestamp("2026-06-01")
START_BOUND = pd.Timestamp("2007-01-01")

def key():
    for line in open(f"{ROOT}/.env.local"):
        if line.startswith("TWELVEDATA_KEY"):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no TWELVEDATA_KEY")

K = key()
CALLS = 0

def fetch(sym, start=None, end=None):
    """One API call. Rate-limited: >=8s spacing + 62s sleep every 8 calls."""
    global CALLS
    if CALLS and CALLS % 8 == 0:
        print("   ... rate-limit sleep 62s (8 req/min) ...", flush=True)
        time.sleep(62)
    url = (f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day"
           f"&outputsize=5000&apikey={K}&format=JSON")
    if start:
        url += f"&start_date={start}"
    if end:
        url += f"&end_date={end}"
    with urllib.request.urlopen(url, timeout=60) as r:
        js = json.loads(r.read().decode())
    CALLS += 1
    time.sleep(8)
    return js

def to_df(js):
    df = pd.DataFrame(js["values"]).rename(columns={"datetime": "date"})
    df["date"] = pd.to_datetime(df["date"])
    df["close"] = df["close"].astype(float)
    return df.sort_values("date").reset_index(drop=True)

def lint(df):
    """Fail-closed gate. Returns (status, detail, metrics)."""
    m = dict(n=len(df), start="", end="", maxgap="", zero_ret="", jumps="")
    if df is None or len(df) < 250:
        return "FAIL(short)", f"n={len(df)}", m
    s = df.set_index("date")["close"].sort_index()
    s = s[s > 0]
    if len(s) < 250:
        return "FAIL(short)", f"n_pos={len(s)}", m
    m.update(n=len(s), start=str(s.index[0].date()), end=str(s.index[-1].date()))
    if s.index[0] > START_BOUND:
        return "FAIL(start)", f"start={m['start']}", m
    if s.index[-1] < FRESH:
        return "FAIL(stale_end)", f"end={m['end']} < {FRESH.date()}", m
    gaps = s.index.to_series().diff().dt.days.dropna()
    mg = int(gaps.max())
    jr = int((s.pct_change().abs() > 0.5).sum())
    zr = int((s.pct_change() == 0).sum())
    m.update(maxgap=mg, jumps=jr, zero_ret=zr)
    if mg > 10:
        return "FAIL(gap)", f"maxgap={mg}d", m
    if jr > 3:
        return "FAIL(jumps)", f"|ret|>50% on {jr}d", m
    return "PASS", f"maxgap={mg}d jumps={jr} zero_ret={zr}", m

def write_pass(sym, df):
    out = df[["date", "close"]].sort_values("date")
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(f"{OUT}/{sym}.csv", index=False)

# ---- (a) must-fetch, plain single call -------------------------------------
PLAIN = [
    ("EWF", "France country; R2 first attempt was HTTP 404, retry (+ARCX fallback)"),
    ("BND", "US total bond agg"),
    ("HYG", "HY credit; expect true start 2007-04 -> document fail honestly"),
    ("DBE", "energy commodity; R1 log said 2007-01 but never wrote; exact recheck"),
]

# ---- (b) R1 start-bound fails, retried with two-window paging --------------
PAGED = [
    ("EWC",  "Canada; true inception 1996 — vendor may hide pre-2008 depth"),
    ("EIS",  "Israel; inception 2008-03 — expect honest fail"),
    ("TUR",  "Turkey; inception 2008-03 — expect honest fail"),
    ("DBP",  "precious metals DB; true inception 2006-01 — candidate PASS"),
    ("USCI", "US commod index; inception 2010-08 — expect honest fail"),
    ("COPX", "copper miners; inception 2010-04 — expect honest fail"),
    ("ENOR", "Norway; inception 2012-01 — expect honest fail"),
    ("EPHE", "Philippines; inception 2010-09 — expect honest fail"),
]

results = []

for sym, why in PLAIN:
    print(f"[a] {sym}: {why}", flush=True)
    try:
        js = fetch(sym)
        if (js.get("status") == "error" or "values" not in js) and sym == "EWF":
            # one fallback: pin the ARCX listing
            url = (f"https://api.twelvedata.com/time_series?symbol=EWF&exchange=ARCX"
                   f"&interval=1day&outputsize=5000&apikey={K}&format=JSON")
            with urllib.request.urlopen(url, timeout=60) as r:
                js = json.loads(r.read().decode())
            CALLS += 1
            time.sleep(8)
        if js.get("status") == "error" or "values" not in js:
            st, det, m = "API_ERR", str(js.get("message", js))[:90], {}
        else:
            df = to_df(js)
            st, det, m = lint(df)
            if st == "PASS":
                write_pass(sym, df)
    except Exception as e:
        st, det, m = "FETCH_FAIL", repr(e)[:90], {}
    results.append(dict(sym=sym, kind="plain", status=st, detail=det, why=why, **m))
    print(f"    -> {st} {det}", flush=True)

for sym, why in PAGED:
    print(f"[b] {sym} (two-window stitch): {why}", flush=True)
    try:
        ja = fetch(sym, start="1995-01-01", end="2012-12-31")
        jb = fetch(sym, start="2013-01-01")
        if ja.get("status") == "error" or "values" not in ja:
            st, det, m = "API_ERR_A", str(ja.get("message", ja))[:90], {}
        elif jb.get("status") == "error" or "values" not in jb:
            st, det, m = "API_ERR_B", str(jb.get("message", jb))[:90], {}
        else:
            da, db = to_df(ja), to_df(jb)
            both = pd.concat([db, da]).drop_duplicates(subset="date", keep="first")  # keep window B (recent) values
            both = both.sort_values("date").reset_index(drop=True)
            seam_dup = int(pd.concat([db, da])["date"].duplicated().sum())
            st, det, m = lint(both)
            m["seam_dup_dropped"] = seam_dup
            m["rows_A"], m["rows_B"] = len(da), len(db)
            if st == "PASS":
                write_pass(sym, both)
    except Exception as e:
        st, det, m = "FETCH_FAIL", repr(e)[:90], {}
    results.append(dict(sym=sym, kind="stitched", status=st, detail=det, why=why, **m))
    print(f"    -> {st} {det}", flush=True)

with open(f"{ROOT}/campaign/agents/chief/coord/DATA_ETF_MORE/work_r2/results_final.json", "w") as f:
    json.dump(results, f, indent=1)

npass = sum(1 for r in results if r["status"] == "PASS")
print(f"\nTOTAL {len(results)} attempted, {npass} PASS, {len(results)-npass} FAIL/ERR")
