import os, sys, json, csv, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import requests
import datalint

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../..")
KEY = None
for line in open(os.path.join(BASE, ".env.local")):
    if line.startswith("TWELVEDATA_KEY="):
        KEY = line.strip().split("=", 1)[1]
OUT = os.path.join(BASE, "tools/quant/data/more_etf")
os.makedirs(OUT, exist_ok=True)

UNIVERSE = ("XLE XLB XLF XLI XLK XLY XLP XLU XLV XLRE XLC KBE KRE ITB XHB SMH IGV XOP XME "
            "GDX GDXJ SLV EEM VWO EFA EWJ EWG EWU EWP EWL EWT EWY EWZ EWW EWA FXI INDA EWK "
            "EWS EID GLD USO UNG TLT IEF SHY LQD HYG AGG JNK TIP VNQ EMB BIL IAU DBC GSG").split()
HAVE_ELSEWHERE = set("XLE XLB XLF XLI EWA GLD HYG IEF LQD TLT AGG".split())
TODO = [s for s in UNIVERSE if s not in HAVE_ELSEWHERE and not os.path.exists(f"{OUT}/{s}.csv")]

results = []
for i, sym in enumerate(TODO):
    # 25-batch checkpoint file so a crash never loses progress
    ckpt = f"{OUT}/.ckpt_{sym}.json"
    payload = None
    try:
        url = ("https://api.twelvedata.com/time_series?symbol=%s&interval=1day"
               "&outputsize=5000&apikey=%s" % (sym, KEY))
        r = requests.get(url, timeout=30)
        if r.status_code == 429:
            time.sleep(30)
            r = requests.get(url, timeout=30)
        j = r.json()
        if j.get("status") != "ok" or not j.get("values"):
            results.append((sym, "FAIL", j.get("errmessage", j.get("message", str(j))[:120])))
            print(f"[{i+1}/{len(TODO)}] {sym} FAIL {results[-1][2]}", flush=True)
            time.sleep(8); continue
        vals = j["values"]
        # empirical ascending check before reversing
        first, last = vals[0]["datetime"], vals[-1]["datetime"]
        descending = first > last
        if descending:
            vals = vals[::-1]
        with open(ckpt, "w") as f:
            json.dump(vals, f)
        # lint BEFORE write
        p = f"{OUT}/{sym}.csv"
        with open(p, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(datalint.COLS)
            for v in vals:
                w.writerow([v.get("datetime"), v.get("open"), v.get("high"),
                            v.get("low"), v.get("close"), v.get("volume", "")])
        try:
            lr = datalint.lint(p)
            results.append((sym, "OK", lr))
            print(f"[{i+1}/{len(TODO)}] {sym} OK {lr['start']}..{lr['end']} rows={lr['rows']} "
                  f"maxgap={lr['max_gap_days']}d zret={lr['zero_ret_rows']} "
                  f"desc_raw={descending}", flush=True)
        except datalint.DataLintError as e:
            os.rename(p, p + ".LINTFAIL")
            results.append((sym, "LINTFAIL", str(e)))
            print(f"[{i+1}/{len(TODO)}] {sym} LINTFAIL {e}", flush=True)
    except Exception as e:
        results.append((sym, "ERR", repr(e)[:120]))
        print(f"[{i+1}/{len(TODO)}] {sym} ERR {results[-1][2]}", flush=True)
    time.sleep(8)

with open(f"{OUT}/.fetch_results.json", "w") as f:
    json.dump(results, f, indent=1)
print("BATCH DONE", len(results))
