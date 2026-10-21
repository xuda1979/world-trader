import sys, os, time, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fred_dl import fetch, lint, detect_freq, write_csv

KEY = os.environ.get("FRED_KEY")
OUT = os.path.dirname(os.path.abspath(__file__))

# (series_id, role) — missing-on-disk list per charter + best-guess IDs for vols/H15
SERIES = [
    ("GASREGCO", "gas"), ("DFOIL", "fuel"), ("GASBREW", "gas"), ("DJFUELUSGULF2", "fuel-dup-check"),
    ("AAA", "credit-m"), ("BAA", "credit-m"), ("DAAA", "credit-d"), ("DBAA", "credit-d"),
    ("BAA10Y", "credit-d"), ("FEDFUNDS", "rates-m"), ("TB3MS", "rates-m"), ("TB6MS", "rates-m"),
    ("DFII5", "real-yield"), ("DFII20", "real-yield"), ("DFII30", "real-yield"),
    ("MZM", "money"), ("REALLN", "credit"), ("TWEXAFEGSMTH", "dollar"),
    ("UNRATE", "macro-m"), ("CPIAUCSL", "macro-m"), ("UMCSENT", "macro-m"),
    ("PERMIT", "macro-m"), ("HOUST", "macro-m"), ("INDPRO", "macro-m"), ("RRSFS", "macro-m"),
    ("DFF", "rates-d"), ("VXVCLS", "vol"), ("OVXCLS", "vol"), ("GVZCLS", "vol"),
    ("MOVE", "vol-bond"), ("H15", "h15-test"),
]
if len(sys.argv) > 1:
    want = set(sys.argv[1].split(","))
    SERIES = [s for s in SERIES if s[0] in want]

results = []
for sid, role in SERIES:
    t0 = time.time()
    (rows, nmiss), err = fetch(sid, KEY)  # full history
    rec = {"series_id": sid, "role": role, "status": "", "freq": "", "n": 0,
           "start": "", "end": "", "missing_codes": 0, "gaps": 0, "max_run": 0,
           "pass": False, "reason": "", "file": "", "secs": 0.0}
    if err is not None:
        rec["status"] = "FAIL:" + err
        results.append(rec)
        print("%-14s %-28s" % (sid, rec["status"]), flush=True)
        time.sleep(0.7)
        continue
    rec["status"] = "ok"
    rec["missing_codes"] = nmiss
    freq = detect_freq(rows)
    rec["freq"] = freq
    if freq == "unknown":
        rec["reason"] = "freq-unknown"
        results.append(rec)
        print("%-14s freq-unknown n=%d" % (sid, len(rows)), flush=True)
        time.sleep(0.7)
        continue
    lr = lint(rows, freq=freq)
    rec.update(n=lr["n"], start=lr["start"], end=lr["end"], gaps=lr["gaps"],
               max_run=lr.get("max_run", 0), pass_=lr["pass"], reason=lr["reason"])
    rec["pass"] = lr["pass"]
    if lr["pass"]:
        fn = os.path.join(OUT, sid + ".csv")
        with open(fn, "w", newline="") as f:
            write_csv(f, rows, sid)
        rec["file"] = fn
    rec["secs"] = round(time.time() - t0, 2)
    results.append(rec)
    print("%-14s %-6s n=%-6d %s..%s gaps=%d maxrun=%s miss=%d %s [%s]" % (
        sid, "PASS" if lr["pass"] else "FAIL", lr["n"], lr["start"], lr["end"],
        lr["gaps"], lr.get("max_run", "-"), nmiss, lr["reason"], freq), flush=True)
    time.sleep(0.7)

# merge into manifest
mfn = os.path.join(OUT, "manifest.csv")
existing = {}
if os.path.exists(mfn):
    with open(mfn) as f:
        for row in csv.DictReader(f):
            existing[row["series_id"]] = row
for rec in results:
    existing[rec["series_id"]] = {
        "series_id": rec["series_id"], "role": rec["role"], "status": rec["status"],
        "freq": rec["freq"], "n": rec["n"], "start": rec["start"], "end": rec["end"],
        "missing_codes": rec["missing_codes"], "gaps": rec["gaps"], "max_run": rec["max_run"],
        "lint_pass": rec["pass"], "reason": rec["reason"], "file": os.path.basename(rec["file"]) if rec["file"] else ""}
with open(mfn, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["series_id","role","status","freq","n","start","end",
        "missing_codes","gaps","max_run","lint_pass","reason","file"])
    w.writeheader()
    for sid in sorted(existing):
        w.writerow(existing[sid])
print("manifest rows:", len(existing))
