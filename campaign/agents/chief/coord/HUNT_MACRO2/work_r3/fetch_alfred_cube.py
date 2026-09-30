#!/usr/bin/env python3
"""HUNT_MACRO2 round 3 — ALFRED vintage cube fetcher (charter 3a).

Fetches, per release series, the FULL vintage episode cube:
every (observation_date, realtime_start=vintage/publication date, value) triple.
ALFRED semantics verified against a known anchor before trusting (see
probe_alfred.py + this script's --verify): PAYEMS obs 2009-11-01 first appears
at realtime_start=2009-12-04 (the actual first-Friday release), so
realtime_start == true first-publication date and each later realtime_start is
a revision release. That is the PIT release calendar.

Output: work_r3/alfred/{SERIES}.csv with columns [obs_date, vintage_date, value]
No synthetic substitutes: any HTTP failure is fatal (fail-closed per charter).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/campaign/agents/chief/coord/HUNT_MACRO2/work_r3/alfred"
os.makedirs(OUT, exist_ok=True)

# (series_id, earliest realtime vintage to fetch, observation_start for the cube)
# realtime_start 2005-01-01: ~21y of monthly releases x ~28y obs history.
SPEC = [
    ("PAYEMS",   "2005-01-01", "2003-01-01"),  # nonfarm payrolls, first Fri 8:30ET
    ("UNRATE",   "2005-01-01", "2003-01-01"),  # unemployment rate, same release
    ("CPIAUCSL", "2005-01-01", "2003-01-01"),  # CPI-U index, mid-month 8:30ET
    ("RSXFS",    "2005-01-01", "2003-01-01"),  # advance retail sales, mid-month
    ("IPMAN",    "2005-01-01", "2003-01-01"),  # industrial production index
    ("UMCSENT",  "2005-01-01", "2003-01-01"),  # consumer sentiment (final)
    ("HOUST",    "2005-01-01", "2003-01-01"),  # housing starts SAAR
    ("DGORDER",  "2005-01-01", "2003-01-01"),  # durable goods orders
    ("ICSA",     "2005-01-01", "2004-01-01"),  # weekly initial claims (Thu 8:30ET)
]
LIMIT = 100000


def fred_key():
    for line in open(f"{ROOT}/.env.local"):
        if line.startswith("FRED_KEY="):
            return line.strip().split("=", 1)[1]
    raise RuntimeError("FRED_KEY not found")


def fetch_page(sid, key, realtime_start, obs_start, offset):
    url = ("https://api.stlouisfed.org/fred/series/observations"
           f"?series_id={sid}&api_key={key}&file_type=json"
           f"&realtime_start={realtime_start}&realtime_end=9999-12-31"
           f"&observation_start={obs_start}&observation_end=9999-12-31"
           f"&limit={LIMIT}&offset={offset}")
    req = urllib.request.Request(url, headers={"User-Agent": "hunt-macro2-r3/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def fetch_series(sid, key, realtime_start, obs_start):
    """Paginate the episode cube. Returns list of (obs_date, vintage_date, value)."""
    rows, offset = [], 0
    while True:
        data = fetch_page(sid, key, realtime_start, obs_start, offset)
        obs = data.get("observations", [])
        count = int(data.get("count", 0))
        for o in obs:
            if o.get("value") in (".", None, ""):
                continue
            rows.append((o["date"], o["realtime_start"], float(o["value"])))
        offset += LIMIT
        if offset >= count or not obs:
            break
        time.sleep(0.4)
    return rows, count


def main():
    key = fred_key()
    print("FRED_KEY present (len=%d)" % len(key))
    summary = {}
    for sid, rt, ospec in SPEC:
        try:
            rows, count = fetch_series(sid, key, rt, ospec)
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            print(f"{sid}: HTTP{e.code} FATAL body={body}")
            summary[sid] = {"http": e.code, "body": body}
            sys.exit(2)  # fail-closed: no partial dataset, no substitutes
        if not rows:
            print(f"{sid}: EMPTY CUBE FATAL")
            sys.exit(2)
        path = f"{OUT}/{sid}.csv"
        with open(path, "w") as f:
            f.write("obs_date,vintage_date,value\n")
            for od, vd, v in sorted(rows):
                f.write(f"{od},{vd},{v!r}\n")
        nvint = len({r[1] for r in rows})
        nobs = len({r[0] for r in rows})
        summary[sid] = {"rows": len(rows), "vintages": nvint, "obs": nobs,
                        "v_first": min(r[1] for r in rows),
                        "v_last": max(r[1] for r in rows)}
        print(f"{sid}: {len(rows)} cube rows, {nvint} vintages "
              f"({min(r[1] for r in rows)}..{max(r[1] for r in rows)}), {nobs} obs periods -> {path}")
    json.dump(summary, open(f"{OUT}/_fetch_summary.json", "w"), indent=1)
    print("ALL FETCHED OK")


if __name__ == "__main__":
    main()
