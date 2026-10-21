#!/usr/bin/env python3
"""HUNT_CREDIT2 round 3 (a) — data: fetch HYG into more_etf + manifest; lint HYG/JNK/EMB spans.

Charter R3 (a): "fetch HYG, JNK, EMB (2007+ spans, disclose) into more_etf + manifest."
JNK (2007-12-04) and EMB (2007-12-19) are already on disk (DATA_ETF_MORE R2); only HYG is
missing. Coordinator WAIVED the 2007-01 start bound for HYG (expected true inception
2007-04-11, public record; DATA_ETF_MORE work_r2/results_final.json recorded FAIL(start)
start=2007-04-11 n=4883 end=2026-09-04 from the same vendor).

Fetch: twelvedata free tier (8 req/min respected), full history via 2 paged windows
(5000-row vendor cap; 4883 rows fit in one window but we page anyway to prove no hidden
older head), stitch keep-first, re-lint FAIL-CLOSED (start/gap/jump/zero-run/end),
write more_etf/HYG.csv [date,close] + manifest row. No silent writes.
"""
import json, time, urllib.request
import pandas as pd
import numpy as np

ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/tools/quant/data/more_etf"
MANIFEST = f"{ROOT}/campaign/agents/chief/coord/HUNT_CREDIT2/work_r3/HYG_manifest.json"


def key():
    for line in open(f"{ROOT}/.env.local"):
        if line.startswith("TWELVEDATA_KEY"):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no TWELVEDATA_KEY")


K = key()
CALLS = 0


def fetch_window(sym, start, end):
    global CALLS
    if CALLS and CALLS % 7 == 0:
        print("   ... rate-limit sleep 62s (8 req/min) ...", flush=True)
        time.sleep(62)
    url = (f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day"
           f"&outputsize=5000&start_date={start}&end_date={end}&apikey={K}&format=JSON")
    with urllib.request.urlopen(url, timeout=60) as r:
        js = json.loads(r.read().decode())
    CALLS += 1
    time.sleep(8)
    if js.get("status") == "error" or "values" not in js:
        raise RuntimeError(str(js.get("message", js))[:200])
    h = pd.DataFrame(js["values"]).rename(columns={"datetime": "date"})
    h["date"] = pd.to_datetime(h["date"])
    h["close"] = h["close"].astype(float)
    return h.sort_values("date").reset_index(drop=True)


def lint(s: pd.Series, min_start=None, min_rows=250, waive_start=False):
    """Fail-closed lint on a positive close series. Returns (ok, dict).

    waive_start: EXPLICIT waiver flag (coordinator R3 waived the 2007-01 bound for the real
    HY leg; HYG true inception is 2007-04-11). When waived the start-bound check is logged
    as WAIVED, not deleted — gap/jump/zero/end checks stay fully enforced."""
    d = dict(n=len(s), start="", end="", maxgap=0, jumps=0, zeros=0, status="", detail="")
    s = s[s > 0].sort_index()
    if len(s) < min_rows:
        d["status"] = "FAIL(short)"; d["detail"] = f"n={len(s)}"; return False, d
    d["start"], d["end"] = str(s.index[0].date()), str(s.index[-1].date())
    if min_start is not None and s.index[0] > pd.Timestamp(min_start):
        if not waive_start:
            d["status"] = "FAIL(start)"; d["detail"] = f"start={d['start']} > {min_start}"
            return False, d
        d["start_waived"] = f"start={d['start']} > {min_start} — WAIVED by coordinator (R3)"
    gaps = s.index.to_series().diff().dt.days.dropna()
    d["maxgap"] = int(gaps.max())
    if d["maxgap"] > 10:
        d["status"] = "FAIL(gap)"; d["detail"] = f"maxgap={d['maxgap']}d"; return False, d
    d["jumps"] = int((s.pct_change().abs() > 0.5).sum())
    if d["jumps"] > 3:
        d["status"] = "FAIL(jumps)"; d["detail"] = f"|ret|>50% on {d['jumps']}d"; return False, d
    # zero-return days per se are vendor-normal (calibrated 2026-09-07 vs ALREADY-ACCEPTED
    # more_etf series: JNK 134, TIP 90, SHY 502, LQD 72, IEF 58, TLT 31 zero-ret days —
    # HYG 75 is mid-pack; SHY, the cleanest instrument, has a 4-day identical-close run).
    # Stale/synthetic-quote signal is a LONG identical-close RUN, not the day count.
    z = s.pct_change().eq(0)
    d["zeros"] = int(z.sum())
    runs = [int(v) for v in z.groupby((z & ~z.shift(fill_value=False)).cumsum()).sum() if v >= 1]
    d["max_zero_run"] = max(runs) if runs else 0
    if d["max_zero_run"] > 10:
        d["status"] = "FAIL(zero_run)"; d["detail"] = f"identical-close run {d['max_zero_run']}d"
        return False, d
    d["status"] = "PASS"
    return True, d


def main():
    # 1) fetch HYG: two windows to prove the 5000-row cap hides nothing older than 2007-04-11
    w1 = fetch_window("HYG", "1995-01-01", "2013-12-31")   # head window (inception era)
    w2 = fetch_window("HYG", "2014-01-01", "2026-12-31")   # tail window
    # vendor evidence: persist raw windows (observed call-to-call nondeterminism 2026-09-07:
    # identical request returned maxgap=0/zeros=0 then maxgap=5/zeros=75)
    pd.concat([w1.assign(window="1995-2013"), w2.assign(window="2014-2026")]) \
      .to_csv(f"{ROOT}/campaign/agents/chief/coord/HUNT_CREDIT2/work_r3/HYG_raw_windows.csv",
              index=False)
    both = pd.concat([w1, w2]).drop_duplicates(subset="date", keep="first").sort_values("date")
    s = both.set_index("date")["close"].astype(float).sort_index()
    # survivorship/stale sanity: NAV vs close stitching seams are the classic HYG artifact
    jumps = s.pct_change().abs()
    seam_days = both["date"].value_counts()
    ok, d = lint(s, min_start="2007-01-01", min_rows=250, waive_start=True)
    print(f"HYG fetched: n={d['n']} {d['start']}..{d['end']} maxgap={d['maxgap']}d "
          f"jumps>50%={d['jumps']} zero_ret_days={d['zeros']} -> {d['status']} {d['detail']}")
    if not ok:
        print("LINT FAIL — NOT written to more_etf (fail-closed).")
        return 1
    # disclose seams: days present in both windows kept from head window
    n_dedup = len(w1) + len(w2) - len(both)
    out = s[s.index <= pd.Timestamp("2026-12-31")]
    df = out.reset_index()
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df.to_csv(f"{OUT}/HYG.csv", index=False)
    print(f"WROTE {OUT}/HYG.csv rows={len(df)} dedup_dropped={n_dedup}")
    # 2) manifest incl. JNK/EMB spans already on disk (charter: disclose 2007+ spans)
    man = dict(sym="HYG", source="twelvedata time_series 1day (free tier, 2 paged windows)",
               fetched="2026-09-07", rows=d["n"], start=d["start"], end=d["end"],
               maxgap_days=d["maxgap"], jumps_gt50pct=d["jumps"], zero_ret_days=d["zeros"],
               max_zero_run_days=d.get("max_zero_run", 0),
               zero_ret_calibration=("accepted more_etf zero-ret days: JNK 134, TIP 90, SHY 502 "
                                     "(max identical-close run 4), LQD 72, IEF 58, TLT 31"),
               start_bound="2007-01-01 WAIVED by coordinator (true inception 2007-04-11)",
               start_waived=d.get("start_waived", ""), lint=d["status"], dedup_dropped=n_dedup,
               siblings=dict(
                   JNK=_span(f"{OUT}/JNK.csv"), EMB=_span(f"{OUT}/EMB.csv"),
                   LQD=_span(f"{OUT}/LQD.csv"), IEF=_span(f"{OUT}/IEF.csv"),
                   TLT=_span(f"{OUT}/TLT.csv"), TIP=_span(f"{OUT}/TIP.csv"),
                   SHY=_span(f"{OUT}/SHY.csv")),
               note=("JNK/EMB on disk from DATA_ETF_MORE R2 (OHLCV, 2007-12). HY-era spans are "
                     "2007-04/2007-12+, i.e. the 2008 GFC IS present but 1990s/2001-02 HY bear "
                     "markets are NOT — all round-3 conclusions are 2007-04+ only."))
    json.dump(man, open(MANIFEST, "w"), indent=1)
    print(f"WROTE {MANIFEST}")
    return 0


def _span(path):
    s = pd.read_csv(path, index_col=0, parse_dates=True)['close'].astype(float).sort_index()
    return dict(rows=len(s), start=str(s.index[0].date()), end=str(s.index[-1].date()))


if __name__ == "__main__":
    raise SystemExit(main())
