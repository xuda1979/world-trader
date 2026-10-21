#!/usr/bin/env python3
"""HUNT_TREASFUT round 7 — ECB SDMX euro-area yield-curve fetch (charter NEW-DATA corner).

Dataflow YC, key family B.U2.EUR.4F.G_N_A.SV_C_YM.SR_<T> = daily par-yield observation of
the euro-area AAA-rated government bond spot yield curve (the ECB's official AAA curve,
estimation described in the ECB's "The euro area government bond yield curve" methodology;
published ~6pm CET for the same business day -> 1-business-day publication lag is honored
PIT by deciding on T+1, plus the T+1 execution shift on top).

Tenors fetched (charter slope + curvature family): SR_1Y, SR_2Y, SR_5Y, SR_10Y, SR_30Y.
Full-span pulls 504 at this endpoint; chunked by calendar year (verified live).

Manifest pins: per-file sha256-16, row counts, first/last obs dates, missing-obs count
(OBS_VALUE blank = ECB missing flag -> dropped, per altdata6 parser convention).
"""
import csv
import hashlib
import io
import json
import os
import socket
import time
import urllib.request

ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/campaign/agents/chief/coord/HUNT_TREASFUT/work_r7/yields"
TENORS = ["1Y", "2Y", "5Y", "10Y", "30Y"]
YEARS = list(range(2004, 2027))          # probe 2004+; earlier years optional (pre-euro-convention)
BASE = "https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_%s"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def fetch_year(tenor, year):
    key = "B.U2.EUR.4F.G_N_A.SV_C_YM.SR_" + tenor
    url = (f"{BASE % tenor}?startPeriod={year}-01-01&endPeriod={year}-12-31&format=csvdata")
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(3):
        try:
            return urllib.request.urlopen(req, timeout=45).read().decode()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(4 * (attempt + 1))


def parse(csv_txt):
    rows = []
    for r in csv.DictReader(io.StringIO(csv_txt)):
        p = (r.get("TIME_PERIOD") or "").strip()
        v = (r.get("OBS_VALUE") or "").strip()
        st = (r.get("OBS_STATUS") or "").strip()
        if p and v:
            rows.append((p, float(v), st))
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = {"source": "ECB Data Portal SDMX 2.1 csvdata (data-api.ecb.europa.eu)",
                "dataflow": "YC", "series": "B.U2.EUR.4F.G_N_A.SV_C_YM (euro-area AAA govt curve)",
                "fetched_utc_note": "chunked by year; per-file sha256_16 + row counts pinned",
                "tenors": {}}
    for t in TENORS:
        allrows = {}
        miss = 0
        for y in YEARS:
            txt = fetch_year(t, y)
            rows = parse(txt)
            miss += sum(1 for r in csv.DictReader(io.StringIO(txt)) if not (r.get("OBS_VALUE") or "").strip())
            for p, v, st in rows:
                allrows[p] = v
        dates = sorted(allrows)
        f = f"{OUT}/ECBAAA_YC_{t}.csv"
        with open(f, "w") as fh:
            fh.write("date,yield_pct\n")
            for d in dates:
                fh.write(f"{d},{allrows[d]!r}\n")
        sha = hashlib.sha256(open(f, "rb").read()).hexdigest()[:16]
        manifest["tenors"][t] = dict(file=f"yields/ECBAAA_YC_{t}.csv", sha256_16=sha,
                                     n=len(dates), first=dates[0], last=dates[-1],
                                     blank_obs_dropped=miss)
        print(f"{t}: n={len(dates)} {dates[0]}..{dates[-1]} blank_dropped={miss} sha16={sha}")
    with open(f"{OUT}/manifest.json", "w") as fh:
        json.dump(manifest, fh, indent=1)
    print("manifest ->", f"{OUT}/manifest.json")


if __name__ == "__main__":
    main()
