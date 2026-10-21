#!/usr/bin/env python3
"""DATA_FREDMORE R7 (a) live-ALFRED cross-check of the RESTORED vintage CSVs.

The 3 vintage files were truncated by the DATA_ORGANIZE 14:40 crash and restored
in place 14:56 from CAMP_BORROW/work_r6/vintage_rebuilt/ (byte-exact). Before
regenerating the manifest rows on top of them, prove the restored bytes equal a
FRESH live ot4 pull from api.stlouisfed.org (not just trust the rebuild).
Exit 0 iff all three series verify.
"""
import csv, json, os, sys, time, urllib.request, urllib.error

ROOT = "/Users/daxu/software/world-trader"
ALFRED = f"{ROOT}/tools/quant/data/alfred"
WORK = os.path.dirname(os.path.abspath(__file__))
KEY = [l.split("=", 1)[1].strip().strip('"').strip("'")
       for l in open(f"{ROOT}/.env.local") if l.startswith("FRED_KEY")][0]

BASE = "https://api.stlouisfed.org/fred/series/observations"


def ot4(sid, retries=4):
    url = (f"{BASE}?series_id={sid}&api_key={KEY}&file_type=json&output_type=4"
           f"&realtime_start=1776-07-04&realtime_end=9999-12-31")
    for a in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.loads(r.read().decode())["observations"], None
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503) and a < retries - 1:
                time.sleep(20)
                continue
            return None, f"HTTP{e.code}"
        except Exception as e:
            if a < retries - 1:
                time.sleep(5)
                continue
            return None, repr(e)[:160]
    return None, "retries-exhausted"


def vintagedates(sid, retries=3):
    url = ("https://api.stlouisfed.org/fred/series/vintagedates?series_id=%s"
           "&api_key=%s&file_type=json" % (sid, KEY))
    for a in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read().decode()).get("vintage_dates", []), None
        except urllib.error.HTTPError as e:
            if e.code == 429 and a < retries - 1:
                time.sleep(20)
                continue
            return [], f"HTTP{e.code}"
        except Exception as e:
            if a < retries - 1:
                time.sleep(5)
                continue
            return [], repr(e)[:160]
    return [], "retries-exhausted"


def fmt(v):
    # alfred_dl.write_vintage_csv convention: ints via %.10g, else repr(float)
    return ("%.10g" % v) if v == int(v) and abs(v) < 1e15 else repr(v)


fails = []
for sid in ["DRALACBS", "DRCLACBS", "WPU05320104"]:
    obs, err = ot4(sid)
    if err:
        print(f"FAIL {sid} live ot4 fetch: {err}")
        fails.append(sid)
        continue
    live = [(o["realtime_start"], o["date"], float(o["value"]))
            for o in obs if o["value"] not in (".", "", None)]
    with open(f"{ALFRED}/{sid}/vintage.csv") as f:
        disk = [(r["release_date"], r["observation_date"], float(r["value"]))
                for r in csv.DictReader(f)]
    # byte-value equality under the write convention
    live_s = [(a, b, fmt(v)) for a, b, v in live]
    disk_s = [(a, b, fmt(v)) for a, b, v in disk]
    eq = live_s == disk_s
    n_mism = sum(1 for x, y in zip(live_s, disk_s) if x != y) + abs(len(live_s) - len(disk_s))
    lags = [(int(__import__("datetime").date.fromisoformat(a).__sub__(
        __import__("datetime").date.fromisoformat(b)).days) for a, b, _ in disk)]
    lag_list = [(__import__("datetime").date.fromisoformat(a)
                 - __import__("datetime").date.fromisoformat(b)).days
                for a, b, _ in disk]
    vd, verr = vintagedates(sid)
    ok = eq
    print(("PASS " if ok else "FAIL ") + f"{sid}: live n={len(live)} disk n={len(disk)} "
          f"value-equal={eq} mism={n_mism} lag {min(lag_list)}..{max(lag_list)}d "
          f"vintagedates n={len(vd)} err={verr} obs_span={disk[0][1]}..{disk[-1][1]} "
          f"rel_span={disk[0][0]}..{disk[-1][0]}")
    if not ok:
        fails.append(sid)
        for i, (x, y) in enumerate(zip(live_s, disk_s)):
            if x != y:
                print(f"   first mismatch at row {i}: live={x} disk={y}")
                break
    time.sleep(0.5)

sys.exit(0 if not fails else 1)
