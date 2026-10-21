#!/usr/bin/env python3
"""DATA_FREDMORE round-3 INDEPENDENT verification (2026-09-07, R3 session).

Re-derives every charter claim from disk + live FRED without using fetch_round3.py's
own bookkeeping, so a bug in the fetcher cannot self-certify. Prints evidence lines;
exit code is 0 only if every check passes (fail-closed).

Run: python3 verify_round3.py
"""
import csv, datetime as dt, json, os, sys, urllib.request

ROOT = "/Users/daxu/software/world-trader"
ALFRED = f"{ROOT}/tools/quant/data/alfred"
MFRED = f"{ROOT}/tools/quant/data/more_fred"
KEY = [l.split("=", 1)[1].strip() for l in open(f"{ROOT}/.env.local")
       if l.startswith("FRED_KEY")][0]

LAG_FLOOR = {"PAYEMS": 27, "UNRATE": 27, "CPIAUCSL": 35, "ICSA": 4, "RSXFS": 37, "IPMAN": 41}
VINTAGE_SERIES = list(LAG_FLOOR)
FAIL7 = ["CPIAUCSL", "UNRATE", "UNRATENSA", "RRSFS", "TEDRATE", "MORTGAGE30US", "GFDEGDQ188S"]

fails = []


def check(label, ok, detail=""):
    print("  [%s] %s %s" % ("PASS" if ok else "FAIL", label, detail))
    if not ok:
        fails.append(label)


def live_ot4_first(sid):
    url = ("%s?series_id=%s&api_key=%s&file_type=json&output_type=4"
           "&realtime_start=1776-07-04&realtime_end=9999-12-31" % (
               "https://api.stlouisfed.org/fred/series/observations", sid, KEY))
    obs = json.loads(urllib.request.urlopen(url, timeout=120).read().decode())["observations"]
    first = {}
    for o in obs:
        if o["date"] not in first and o["value"] not in (".", "", None):
            first[o["date"]] = (o["realtime_start"], o["value"])
    return first


def bday_runs(dates):
    have = set(dates)
    a, b = dt.date.fromisoformat(dates[0]), dt.date.fromisoformat(dates[-1])
    runs, cur, d = [], None, a
    while d <= b:
        if d.weekday() < 5 and d.isoformat() not in have:
            cur = cur or d
        elif d.weekday() < 5:
            if cur:
                runs.append((cur, d - dt.timedelta(days=1)))
            cur = None
        d += dt.timedelta(days=1)
    if cur:
        runs.append((cur, b))
    return runs


def n_bdays(r):
    n, d = 0, r[0]
    while d <= r[1]:
        n += d.weekday() < 5
        d += dt.timedelta(days=1)
    return n


print("=== (a) vintages: structure, lag floor, live equality ===")
for sid in VINTAGE_SERIES:
    p = f"{ALFRED}/{sid}/vintage.csv"
    if not os.path.exists(p):
        check(f"{sid} file", False)
        continue
    rows = list(csv.reader(open(p)))[1:]
    rel = [r[0] for r in rows]
    obs = [r[1] for r in rows]
    lags = [(dt.date.fromisoformat(a) - dt.date.fromisoformat(b)).days for a, b in zip(rel, obs)]
    check(f"{sid} n>=200", len(rows) >= 200, "n=%d" % len(rows))
    check(f"{sid} unique obs (PIT)", len(set(obs)) == len(obs))
    check(f"{sid} lag>=%d all rows" % LAG_FLOOR[sid], min(lags) >= LAG_FLOOR[sid],
          "min=%d max=%d" % (min(lags), max(lags)))
    check(f"{sid} sorted by (rel,obs)",
          all((rel[i], obs[i]) < (rel[i + 1], obs[i + 1]) for i in range(len(rows) - 1)))
    live = live_ot4_first(sid)
    mm = [(r[1], r[0], r[2]) for r in rows
          if r[1] in live and (live[r[1]][0] != r[0] or float(live[r[1]][1]) != float(r[2]))]
    check(f"{sid} live==disk first-release", len(mm) == 0,
          "disk_n=%d live_n=%d mismatches=%d %s" % (len(rows), len(live), len(mm), mm[:1]))

print("=== (a2) PIT sanity vs historical release record ===")
pay = {r[1]: r for r in list(csv.reader(open(f"{ALFRED}/PAYEMS/vintage.csv")))[1:]}
un = {r[1]: r for r in list(csv.reader(open(f"{ALFRED}/UNRATE/vintage.csv")))[1:]}
ics = {r[1]: r for r in list(csv.reader(open(f"{ALFRED}/ICSA/vintage.csv")))[1:]}
check("PAYEMS 2020-03 first print 151786 @2020-04-03", pay["2020-03-01"] == ["2020-04-03", "2020-03-01", "151786"], str(pay["2020-03-01"]))
check("UNRATE 2020-04 first print 14.7 @2020-05-08", un["2020-04-01"] == ["2020-05-08", "2020-04-01", "14.7"], str(un["2020-04-01"]))
check("ICSA wk2020-03-21 first print 3283000 @2020-03-26", ics["2020-03-21"] == ["2020-03-26", "2020-03-21", "3283000"], str(ics["2020-03-21"]))

print("=== (a3) 2025-10 BLS hole reflected in vintages ===")
for sid in ("UNRATE", "CPIAUCSL"):
    obs = [r[1] for r in list(csv.reader(open(f"{ALFRED}/{sid}/vintage.csv")))[1:]]
    check(f"{sid} vintage has no 2025-10-01", "2025-10-01" not in obs)

print("=== (b) FAIL7 reconciliation: data facts ===")
g = [r[0] for r in list(csv.reader(open(f"{MFRED}/GFDEGDQ188S.csv")))[1:]]
gd = [dt.date.fromisoformat(x) for x in g]
check("GFDEGDQ188S 100% on quarterly grid", all(d.day == 1 and d.month in (1, 4, 7, 10) for d in gd))
y, m = gd[0].year, gd[0].month
slots = []
while (y, m) <= (gd[-1].year, gd[-1].month):
    slots.append(dt.date(y, m, 1))
    m += 3
    if m > 12:
        y, m = y + 1, m - 12
check("GFDEGDQ188S 241/241 slots", len(slots) == len(g) == 241 and not (set(slots) - set(gd)),
      "slots=%d rows=%d" % (len(slots), len(g)))

mm = [dt.date.fromisoformat(r[0]) for r in list(csv.reader(open(f"{MFRED}/MORTGAGE30US.csv")))[1:]]
sps = [(mm[i + 1] - mm[i]).days for i in range(len(mm) - 1)]
check("MORTGAGE30US max spacing <=9d (no absent week)", max(sps) <= 9, "max=%dd" % max(sps))

tds = [r[0] for r in list(csv.reader(open(f"{MFRED}/TEDRATE.csv")))[1:]]
runs = bday_runs(tds)
lens = sorted({n_bdays(r) for r in runs}, reverse=True)
check("TEDRATE max missing-bday run == 3", lens[0] == 3, "distinct run lens=%s" % lens[:3])
check("TEDRATE len-3 runs == 5 Christmas clusters",
      sorted(r[0].year for r in runs if n_bdays(r) == 3) == [1993, 1999, 2004, 2010, 2021])
check("TEDRATE 1986-01-20 ABSENT (MLK 1986)", "1986-01-20" not in set(tds))
check("TEDRATE 1986-01-20 isolated 1-bday gap (neighbors present)",
      "1986-01-17" in set(tds) and "1986-01-21" in set(tds))

rsa = {r[0]: r[1] for r in list(csv.reader(open(f"{MFRED}/RSAFS.csv")))[1:]}
rrs = {r[0]: r[1] for r in list(csv.reader(open(f"{MFRED}/RRSFS.csv")))[1:]}
cp = [r[0] for r in list(csv.reader(open(f"{MFRED}/CPALTT01USM657N.csv")))[1:]]
check("RSAFS HAS 2025-10 (731051) / RRSFS missing it",
      "2025-10-01" in rsa and rsa["2025-10-01"] == "731051" and "2025-10-01" not in rrs)
check("CPALTT01USM657N (CPI deflator) absent 2025-09..11",
      not any("2025-1" in d or d == "2025-09-01" for d in cp))

print("=== (c) manifest honesty ===")
rows = list(csv.DictReader(open(f"{MFRED}/manifest.csv")))
man = {r["series_id"]: r for r in rows}
ids = [r["series_id"] for r in rows]
check("no duplicate series_id rows", len(ids) == len(set(ids)), "rows=%d" % len(rows))
hdr = set(next(csv.reader(open(f"{MFRED}/manifest.csv"))))
check("header covers all row keys (no truncated write)", not ({k for r in rows for k in r} - hdr))
for sid in FAIL7:
    check(f"{sid} reconciled_r3=True", man[sid].get("reconciled_r3") == "True")
    check(f"{sid} reason>=30 chars", len(man[sid].get("reason", "")) > 30)
check("TEDRATE reason no false '1986-01-20 has data'",
      "1986-01-20 has data" not in man["TEDRATE"]["reason"] and
      "1986-01-20 absent" in man["TEDRATE"]["reason"])
check("MORTGAGE30US reclassified PASS (holiday-tolerant weekly)", man["MORTGAGE30US"]["lint_pass"] == "True")
check("GFDEGDQ188S reclassified PASS (quarterly)", man["GFDEGDQ188S"]["lint_pass"] == "True")
for sid in ("CPIAUCSL", "UNRATE", "UNRATENSA", "RRSFS", "TEDRATE"):
    check(f"{sid} stays FAIL (lint is law)", man[sid]["lint_pass"] == "False")
    # charter (b): backfill attempt or documented-why. TEDRATE gaps are NYSE closures
    # (no observation ever existed -> nothing to backfill; marker is STRUCTURAL);
    # the four BLS-hole rows are missing-but-publishable months (backfill=impossible).
    if sid == "TEDRATE":
        check("TEDRATE structural-why recorded", "STRUCTURAL" in man["TEDRATE"]["reason"])
    else:
        check(f"{sid} backfill reason recorded", "backfill=impossible" in man[sid]["reason"])
check("no files deleted", all(os.path.exists(f"{MFRED}/{s}.csv") for s in FAIL7))
for sid in VINTAGE_SERIES:
    r = man[f"ALFRED:{sid}"]
    check(f"ALFRED:{sid} vintage=True lag_days", r["vintage"] == "True" and int(r["lag_days"]) == LAG_FLOOR[sid])
check("ALFRED:SP500 loud drop recorded", man["ALFRED:SP500"]["lint_pass"] == "False"
      and not os.path.exists(f"{ALFRED}/SP500/vintage.csv"))
for sid in ("VIXCLS", "DGS10", "DEXJPUS"):
    check(f"ALFRED:{sid} no false no-vintages claim",
          f"ALFRED:{sid}" not in man or "no-vintages" not in man[f"ALFRED:{sid}"]["reason"])
for r in rows:
    if r["lint_pass"] != "True":
        continue
    f = r.get("file", "")
    cands = [os.path.join(MFRED, f), os.path.join(ROOT, f), f]
    if not f or not any(os.path.exists(c) for c in cands):
        check(f"PASS-row file exists: {r['series_id']}", False, f)
print("  [..] PASS-row=>file invariant swept all rows")

print()
if fails:
    print("VERIFY FAIL-CLOSED: %d failed -> %s" % (len(fails), fails))
    sys.exit(1)
print("VERIFY OK: all round-3 charter claims reproduce from disk + live FRED.")
