# Daily developed-market rates legs the estate was missing (all keyless, free).
#
# Extends the same axis bund_daily opened for Germany. A full survey of the
# estate's curves found GBP (boe_curve, 1979+), JPY (mof_jgb, 1974+), EUR (ecb_yc),
# DE (bund_daily) -- but NO Australian, Canadian or Norwegian leg anywhere. These
# three sources are official central-bank endpoints, keyless, and daily:
#
#   * RBA (Australia)   rba.gov.au/statistics/tables/csv/f{1,2}-data.csv
#                       Official CSV. F1 = money market (cash rate target,
#                       interbank overnight), F2 = AGS bond curve (2/3/5/10y).
#                       WARNING: the CURRENT day's row is only partly populated
#                       (2026-09-11 carried just the Total Return Index), and F2
#                       publishes on a lag (9 days at probe time). So columns are
#                       indexed by header NAME, never by position, and the
#                       staleness allowance is per series.
#   * BoC (Canada)      bankofcanada.ca/valet/observations/<SERIES>/json
#                       Valet. 2/3/5/10y benchmark yields + a long-term series,
#                       daily since 2001-01-02 -- the longest daily span here.
#                       Each observation value arrives as a nested object under a
#                       "v" key, and is empty on holidays.
#   * Norges Bank       data.norges-bank.no/api/data/IR/B.KPRA.SD.R
#                       SDMX-CSV (semicolon-delimited), key policy rate daily
#                       since 1991-01-01.
#
# Each country keeps its own holiday calendar, so lint allows isolated runs of up
# to `maxrun_tol` missed business days and still fails a longer contiguous hole --
# the same policy em_rates uses.
import csv
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data", "dm_rates")

RBA = "https://www.rba.gov.au/statistics/tables/csv/%s-data.csv"
BOC = "https://www.bankofcanada.ca/valet/observations/%s/json?start_date=1990-01-01"
NORGES = "https://data.norges-bank.no/api/data/IR/B.KPRA.SD.R?format=csv&startPeriod=1990-01-01"

# (name, source, arg, freq, lo, hi, min_rows, max_stale_days)
SERIES = [
    ("aud_cash_rate_target", "rba_f1", "Cash Rate Target", "daily", -1.0, 25.0, 500, 10),
    ("aud_interbank_overnight", "rba_f1", "Interbank Overnight Cash Rate", "daily", -1.0, 30.0, 500, 10),
    ("aud_govt_2y", "rba_f2", "Australian Government 2 year bond", "daily", -3.0, 25.0, 500, 20),
    ("aud_govt_3y", "rba_f2", "Australian Government 3 year bond", "daily", -3.0, 25.0, 500, 20),
    ("aud_govt_5y", "rba_f2", "Australian Government 5 year bond", "daily", -3.0, 25.0, 500, 20),
    ("aud_govt_10y", "rba_f2", "Australian Government 10 year bond", "daily", -3.0, 25.0, 500, 20),
    ("cad_govt_2y", "boc", "BD.CDN.2YR.DQ.YLD", "daily", -3.0, 25.0, 2000, 10),
    ("cad_govt_3y", "boc", "BD.CDN.3YR.DQ.YLD", "daily", -3.0, 25.0, 2000, 10),
    ("cad_govt_5y", "boc", "BD.CDN.5YR.DQ.YLD", "daily", -3.0, 25.0, 2000, 10),
    ("cad_govt_10y", "boc", "BD.CDN.10YR.DQ.YLD", "daily", -3.0, 25.0, 2000, 10),
    ("cad_govt_long", "boc", "BD.CDN.LONG.DQ.YLD", "daily", -3.0, 25.0, 2000, 10),
    ("nok_policy_rate", "norges", "B.KPRA.SD.R", "daily", -1.0, 20.0, 2000, 10),
]


def _get(url, timeout=90, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url, headers=dict([("User-Agent", UA), ("Accept", "*/*")]))
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8-sig", "replace"), None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(4 * (attempt + 1))
                continue
            return None, repr(e)[:140]
    return None, "retries-exhausted"


def _num(cell):
    if cell is None:
        return None
    s = str(cell).strip().replace(",", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_rba(text, want):
    # Columns are located by header NAME. The current day's row is only partly
    # populated, so a positional index can read the wrong column on that row.
    ls = [l for l in text.splitlines() if l.strip()]
    hi = None
    for i, l in enumerate(ls):
        if l.startswith("Title,"):
            hi = i
            break
    if hi is None:
        raise ValueError("RBA header row not found")
    hdr = [h.strip() for h in ls[hi].split(",")]
    idx = dict((h, j) for j, h in enumerate(hdr))
    miss = [w for w in want if w not in idx]
    if miss:
        raise ValueError("RBA columns missing (header changed?): %s" % miss)
    out = dict((w, []) for w in want)
    for l in ls[hi + 1:]:
        cells = l.split(",")
        try:
            d = dt.datetime.strptime(cells[0].strip(), "%d-%b-%Y").date().isoformat()
        except ValueError:
            continue
        for w in want:
            j = idx[w]
            v = _num(cells[j]) if j < len(cells) else None
            if v is not None:
                out[w].append((d, v))
    return out


def parse_boc(text, series):
    rows = []
    for o in json.loads(text).get("observations", []):
        cell = o.get(series)
        v = _num(cell.get("v")) if isinstance(cell, dict) else None
        if v is not None and o.get("d"):
            rows.append((o["d"], v))
    return rows


def parse_norges(text):
    ls = [l for l in text.splitlines() if l.strip()]
    hdr = [h.strip() for h in ls[0].split(";")]
    if "TIME_PERIOD" not in hdr or "OBS_VALUE" not in hdr:
        raise ValueError("Norges SDMX header changed: %s" % hdr[:6])
    ti, vi = hdr.index("TIME_PERIOD"), hdr.index("OBS_VALUE")
    rows = []
    for l in ls[1:]:
        c = l.split(";")
        if len(c) <= max(ti, vi):
            continue
        v = _num(c[vi])
        if v is not None:
            rows.append((c[ti].strip(), v))
    return rows


def lint_daily(rows, lo, hi, today, min_rows, maxrun_tol=5, max_stale_days=10):
    # Fail-closed: order/dupe, plausibility, length, contiguous hole longer than
    # this market's own holiday runs, and a staleness ceiling (RBA F2 publishes on
    # a lag, so its ceiling is looser than the others).
    res = dict(n=len(rows), ok=False, reason="", gaps=0, max_run=0, stale_days=None)
    if not rows:
        res["reason"] = "empty"
        return res
    dates = [dt.date.fromisoformat(r[0]) for r in rows]
    if any(dates[i] >= dates[i + 1] for i in range(len(dates) - 1)):
        res["reason"] = "order/dupe"
        return res
    res["start"], res["end"] = dates[0].isoformat(), dates[-1].isoformat()
    if any((v != v) or not (lo <= v <= hi) for _, v in rows):
        res["reason"] = "implausible"
        return res
    if res["n"] < min_rows:
        res["reason"] = "n<min(%d<%d)" % (res["n"], min_rows)
        return res
    have, d, run, maxrun, miss = set(dates), dates[0], 0, 0, 0
    while d <= dates[-1]:
        if d.weekday() < 5:
            if d in have:
                run = 0
            else:
                run += 1
                miss += 1
                maxrun = max(maxrun, run)
        d += dt.timedelta(days=1)
    res["gaps"], res["max_run"] = miss, maxrun
    if maxrun > maxrun_tol:
        res["reason"] = "contiguous-hole=%d" % maxrun
        return res
    stale = (today - dates[-1]).days
    res["stale_days"] = stale
    if stale > max_stale_days:
        res["reason"] = "stale=%dd>%d" % (stale, max_stale_days)
        return res
    res["ok"] = True
    res["reason"] = "ok"
    return res


def fetch_source(src, args):
    # One network call per source where the endpoint serves all its columns at once.
    if src in ("rba_f1", "rba_f2"):
        text, err = _get(RBA % src.split("_")[1])
        if err:
            return dict(), err
        return parse_rba(text, args), None
    if src == "boc":
        out = dict()
        for a in args:
            text, err = _get(BOC % a)
            out[a] = parse_boc(text, a) if not err else []
            time.sleep(0.5)
        return out, None
    if src == "norges":
        text, err = _get(NORGES)
        if err:
            return dict(), err
        return dict((a, parse_norges(text)) for a in args), None
    return dict(), "unknown source " + src


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    today = dt.date.today()
    by_src = dict()
    for row in SERIES:
        by_src.setdefault(row[1], []).append(row[2])
    cache = dict()
    for src, args in by_src.items():
        rows_by_arg, err = fetch_source(src, args)
        cache[src] = rows_by_arg
        if err:
            print("WARN %s fetch: %s" % (src, err))
    ok, failed = 0, []
    with open(os.path.join(OUT, "manifest.csv"), "w", newline="") as man:
        w = csv.writer(man)
        w.writerow(["family", "file", "date_col", "kind", "rows", "cols", "exception"])
        for name, src, arg, freq, lo, hi, mn, stale in SERIES:
            rows = cache.get(src, dict()).get(arg, [])
            res = lint_daily(rows, lo, hi, today, mn, max_stale_days=stale)
            if not res["ok"]:
                failed.append((name, res["reason"]))
                print("FAIL %-26s %s" % (name, res["reason"]))
                continue
            with open(os.path.join(OUT, name + ".csv"), "w", newline="") as f:
                f.write("date,value\n")
                for d, v in rows:
                    f.write("%s,%s\n" % (d, repr(v)))
            w.writerow(["dm_rates", name + ".csv", "date", "timeseries", str(res["n"]),
                        "2", "src=%s gaps=%d maxrun=%d stale=%dd"
                        % (src, res["gaps"], res["max_run"], res["stale_days"])])
            ok += 1
            print("OK   %-26s n=%-5d %s..%s gaps=%d stale=%dd"
                  % (name, res["n"], res["start"], res["end"], res["gaps"], res["stale_days"]))
    print("dm_rates: %d ok, %d failed" % (ok, len(failed)))
    if failed:
        print("failures: " + "; ".join("%s=%s" % t for t in failed))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
