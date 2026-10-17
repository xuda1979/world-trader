#!/usr/bin/env python3
"""ITER62 wave-1 (2026-10-16): append-only extend of the 8 remaining S9 sector-ETF
leaves (XLK XLY XLP XLE XLF XLV XLI XLB) from TwelveData. XLU/IEF already extended
(td_extend_report.json, exact overlap maxdev=0). Fail-closed: overlap must be EXACT
(maxdev == 0.0) vs on-disk more_etf CSVs; snapshot pre-state before append.
8 req/min rate limit honored (sleep 8s)."""
import json, os, shutil, sys, time, urllib.request

ROOT = "/Users/daxu/software/world-trader"
WORK = os.path.join(ROOT, "campaign/work_backtest_oos/refresh_2026_10_16")
ETFDIR = os.path.join(ROOT, "tools/quant/data/more_etf")

key = None
for line in open(os.path.join(ROOT, ".env.local")):
    if line.strip().startswith("TWELVEDATA_KEY"):
        key = line.split("=", 1)[1].strip().strip('"').strip("'")
if not key:
    print("FATAL: TWELVEDATA_KEY not found in .env.local"); sys.exit(1)

TICKERS = ["XLK", "XLY", "XLP", "XLE", "XLF", "XLV", "XLI", "XLB"]

def fetch(sym):
    url = (f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day"
           f"&outputsize=5000&apikey={key}&format=JSON")
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode())

snapdir = os.path.join(WORK, "td_leaf_snapshot_pre")
os.makedirs(snapdir, exist_ok=True)

report = {}
fail = False
for i, sym in enumerate(TICKERS):
    if i:
        time.sleep(8)  # 8 req/min
    d = fetch(sym)
    if d.get("status") != "ok":
        print(f"{sym}: FETCH FAIL {d.get('code')} {d.get('message','')[:120]}")
        report[sym] = {"action": "FETCH_FAIL", "code": d.get("code"),
                       "message": d.get("message", "")[:200]}
        fail = True
        continue
    rows = sorted((v["datetime"][:10], float(v["close"])) for v in d["values"])
    path = os.path.join(ETFDIR, f"{sym}.csv")
    disk_lines = open(path).read().splitlines()
    body = disk_lines[1:]
    disk = {}
    for line in body:
        dt, c = line.split(",")
        disk[dt] = float(c)
    ov = [(dt, c, disk[dt]) for dt, c in rows if dt in disk]
    dev = max((abs(a - b) for _, a, b in ov), default=0.0)
    new_rows = [(dt, c) for dt, c in rows if dt not in disk]
    if dev != 0.0:
        print(f"{sym}: OVERLAP DEVIATION {dev} - SKIPPED (fail-closed)")
        report[sym] = {"action": "SKIPPED_DEVIATION", "overlap_n": len(ov),
                       "overlap_maxdev": dev}
        fail = True
        continue
    if not new_rows:
        print(f"{sym}: no new rows (disk ends {max(disk)})")
        report[sym] = {"action": "no_new_rows", "final_last": max(disk)}
        continue
    shutil.copy2(path, os.path.join(snapdir, f"{sym}.csv"))
    with open(path, "a") as f:
        for dt, c in new_rows:
            f.write(f"{dt},{c}\n")
    body2 = open(path).read().splitlines()[1:]
    report[sym] = {
        "overlap_n": len(ov), "overlap_maxdev": dev,
        "committed_last": max(disk), "new_rows": len(new_rows),
        "new_first": new_rows[0][0], "new_last": new_rows[-1][0],
        "final_n": len(body2), "final_last": body2[-1].split(",")[0],
        "action": f"extended -> {new_rows[-1][0]} (n={len(body2)})",
    }
    print(f"{sym}: overlap n={len(ov)} maxdev=0 exact; appended {len(new_rows)} "
          f"rows -> {new_rows[-1][0]} (n={len(body2)})")

out = os.path.join(WORK, "td_extend_report.json")
old = {}
if os.path.exists(out):
    old = json.load(open(out))
old.update(report)
json.dump(old, open(out, "w"), indent=1)
print("wrote", out)
if fail:
    print("STATUS: FAIL (see report)"); sys.exit(1)
print("STATUS: OK")
