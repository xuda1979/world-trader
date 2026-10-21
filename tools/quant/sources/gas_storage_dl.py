# GIE AGSI European gas storage -- keyless, free, daily since 2011-01-01.
#
# New axis: nothing in the estate covers European energy. This is the physical
# storage balance that drives TTF gas and, through it, EU power and inflation.
#
# API notes learned by probing (all of these bit):
#   * Data is served NEWEST-FIRST and paginated. Default page size is 30 -> 192
#     pages for the EU series; passing size=300 cuts that to 20.
#   * The `from=` filter is unreliable for long ranges (an EU query with
#     from=2011-01-01 returned a 30-row default page and last_page=192, while
#     from=2026-09-01 correctly returned 9 rows). So this module paginates rather
#     than trusting a date filter.
#   * The date field is `gasDayStart`, not `gas_day` (which only appears on the
#     envelope). Several numeric fields arrive as STRINGS.
#   * Gas days are CALENDAR days -- weekends included (191 pages of 30 + 1 covers
#     2011-01-01..2026-09-09 exactly). lint_cal therefore counts calendar gaps,
#     not business-day gaps. Reusing the business-day policy here would have
#     declared every weekend a hole.
import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "data", "gas_storage")
API = "https://agsi.gie.eu/api/data/%s?from=%s&to=%s&page=%d&size=%d"
PAGE_SIZE = 300

# Both datasets report from 2011-01-01. A pull starting materially later means
# pagination truncated (see fetch_dataset) -- catches it even when the truncated
# row count still clears min_rows.
DATASET_START = dict([("EU", "2011-01-01"), ("DE", "2011-01-01")])

# (name, dataset, field, lo, hi, min_rows)
SERIES = [
    ("eu_storage_full_pct", "EU", "full", 0.0, 100.0, 2000),
    ("eu_gas_in_storage_twh", "EU", "gasInStorage", 0.0, 2000.0, 2000),
    ("eu_net_withdrawal_gwh_d", "EU", "netWithdrawal", -8000.0, 15000.0, 2000),
    ("eu_injection_gwh_d", "EU", "injection", 0.0, 8000.0, 2000),
    ("eu_withdrawal_gwh_d", "EU", "withdrawal", 0.0, 15000.0, 2000),
    ("de_storage_full_pct", "DE", "full", 0.0, 110.0, 2000),
    ("de_net_withdrawal_gwh_d", "DE", "netWithdrawal", -6000.0, 6000.0, 2000),
]


def _get(url, timeout=90, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url, headers=dict([("User-Agent", UA), ("Accept", "*/*")]))
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", "replace")), None
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


def _fetch_window(code, frm, to):
    # Pages INSIDE one bounded window until a page is empty or repeats a date.
    rows, page, seen, err = [], 1, set(), None
    while page <= 12:
        j, e = _get(API % (code, frm, to, page, PAGE_SIZE))
        if e:
            err = e
            break
        chunk = j.get("data") or []
        if not chunk:
            break
        if not any(str(r.get("gasDayStart")) not in seen for r in chunk):
            break
        for r in chunk:
            seen.add(str(r.get("gasDayStart")))
        rows.extend(chunk)
        page += 1
        time.sleep(0.3)
    return rows, err


def fetch_dataset(code, y0=2011):
    # -> (list_of_rows, err). Chunked BY YEAR, and each year is row-count verified.
    #
    # WHY NOT global pagination: it is silently lossy. The EU series came back as
    # 3,900 rows (2016-01-06..) on one run and 5,731 rows (2011-01-01..) on the
    # next, err=None both times, and DE served just its first page (300 rows,
    # 2025-11-14..) on a third -- the endpoint intermittently reports a short
    # last_page or an empty page 2. Across the whole series that quietly drops
    # years. Inside a ONE-YEAR window the same failure is obvious, because a
    # complete year has ~365 gas days, so each chunk is checked and retried once
    # before being called short.
    today = dt.date.today()
    rows, errs = [], []
    for y in range(y0, today.year + 1):
        frm = "%d-01-01" % y
        to = today.isoformat() if y == today.year else "%d-12-31" % y
        expect_min = 200 if y == today.year else 350
        chunk, err = _fetch_window(code, frm, to)
        got = len(set(str(r.get("gasDayStart")) for r in chunk))
        if err or got < expect_min:
            time.sleep(2.0)
            chunk, err = _fetch_window(code, frm, to)
            got = len(set(str(r.get("gasDayStart")) for r in chunk))
        if err:
            errs.append("%d=%s" % (y, err))
        elif got < expect_min:
            errs.append("%d=short(%d<%.0f)" % (y, got, expect_min))
        rows.extend(chunk)
        time.sleep(0.3)
    return rows, ("; ".join(errs) if errs else None)


def parse_rows(rows, field):
    pts = []
    for r in rows:
        d = r.get("gasDayStart")
        v = _num(r.get(field))
        if d and v is not None:
            pts.append((str(d)[:10], v))
    return sorted(set(pts))


def lint_cal(rows, lo, hi, today, min_rows, maxrun_tol=3, max_stale_days=3,
             expect_start=None):
    # Calendar-day census (gas days include weekends). A short run of missing days
    # is tolerated -- AGSI occasionally revises a day away -- but a longer
    # contiguous hole, or a stale tail, fails.
    res = dict(n=len(rows), ok=False, reason="", gaps=0, max_run=0, stale_days=None)
    if not rows:
        res["reason"] = "empty"
        return res
    dates = [dt.date.fromisoformat(r[0]) for r in rows]
    if any(dates[i] >= dates[i + 1] for i in range(len(dates) - 1)):
        res["reason"] = "order/dupe"
        return res
    res["start"], res["end"] = dates[0].isoformat(), dates[-1].isoformat()
    if expect_start is not None and res["start"] > expect_start:
        res["reason"] = "truncated-start=%s (expected<=%s)" % (res["start"], expect_start)
        return res
    if any((v != v) or not (lo <= v <= hi) for _, v in rows):
        res["reason"] = "implausible"
        return res
    if res["n"] < min_rows:
        res["reason"] = "n<min(%d<%d)" % (res["n"], min_rows)
        return res
    have, d, run, maxrun, miss = set(dates), dates[0], 0, 0, 0
    while d <= dates[-1]:
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


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    today = dt.date.today()
    datasets = sorted(set(r[1] for r in SERIES))
    raw, errs = dict(), dict()
    for code in datasets:
        rows, err = fetch_dataset(code)
        raw[code] = rows
        if err:
            errs[code] = err
        print("fetched %-3s rows=%-5d %s" % (code, len(rows), ("ERR " + err) if err else "ok"),
              flush=True)
    ok, failed = 0, []
    with open(os.path.join(OUT, "manifest.csv"), "w", newline="") as man:
        w = csv.writer(man)
        w.writerow(["family", "file", "date_col", "kind", "rows", "cols", "exception"])
        for name, code, field, lo, hi, mn in SERIES:
            pts = parse_rows(raw.get(code, []), field)
            res = lint_cal(pts, lo, hi, today, mn,
                           expect_start=DATASET_START.get(code))
            if not res["ok"]:
                failed.append((name, res["reason"]))
                print("FAIL %-26s %s" % (name, res["reason"]))
                continue
            with open(os.path.join(OUT, name + ".csv"), "w", newline="") as f:
                f.write("date,value\n")
                for d, v in pts:
                    f.write("%s,%s\n" % (d, repr(v)))
            w.writerow(["gas_storage", name + ".csv", "date", "timeseries", str(res["n"]),
                        "2", "src=agsi dataset=%s field=%s gaps=%d maxrun=%d stale=%dd"
                        % (code, field, res["gaps"], res["max_run"], res["stale_days"])])
            ok += 1
            print("OK   %-26s n=%-5d %s..%s gaps=%d stale=%dd"
                  % (name, res["n"], res["start"], res["end"], res["gaps"], res["stale_days"]))
    print("gas_storage: %d ok, %d failed" % (ok, len(failed)))
    if failed:
        print("failures: " + "; ".join("%s=%s" % t for t in failed))
    if errs:
        print("fetch errors: " + "; ".join("%s=%s" % t for t in errs.items()))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
