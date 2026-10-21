"""DATA_FREDMORE R4 / DATA_CBOEHIST: enumerate MAX keyless CBOE per-symbol &
strategy index history via cdn.cboe.com/api/global/us_indices/daily_prices/
{SYM}_History.csv (the only keyless CBOE endpoint family that serves HISTORY;
all put_call_ratios + charts/historical/volumes routes 403 -- see probe_history_endpoints.py).

Method: probe CBOE's own published index-symbol roster (single-stock/equity-vol
indexes VX*, ETP/commodity vol indexes, option-strategy indexes). No auth, no
scraping workarounds (AAII/FINRA precedent). Control = VIX (known-good 200).
Output: probe_roster_out.json + printed table.
"""
import json, ssl, sys, time, urllib.request, urllib.error

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (research; world-trader free-data harvest)"
BASE = "https://cdn.cboe.com/api/global/us_indices/daily_prices/%s_History.csv"

CONTROL = "VIX"

# CBOE-published index symbols (prospectus/web rosters, incl. discontinued)
CANDIDATES = [
    # single-stock equity vol indexes (CBOE Equity VolIndex family, 2011)
    "VXAPL","VXAMZN","VXAXP","VXBA","VXCSCO","VXEBAY","VXF","VXFCX","VXGOOG","VXGOOGL",
    "VXGS","VXIBM","VXINTC","VXJNJ","VXJPM","VXKO","VXMCD","VXMMM","VXMSFT","VXNFLX",
    "VXOXY","VXPFE","VXPG","VXT","VXUPS","VXVZ","VXWMT","VXXOM","VXGM","VXTSLA",
    # ETP / commodity / intl vol indexes
    "VXGDX","VXGLD","VXSLV","VXUSO","VXEEM","VXEW","VXFXI","VXVXX","VXUP","VXDN",
    # option-strategy / flow indexes
    "BXM","BXY","BXMD","PUT","PUTR","WPUT","PPUT","CLL","CLL30","CLL60","CLL80",
    "CLL95","CLL100","CLL115","CLL130","XMPT","SNIFEWS","LOVOL","TDOL",
    # aggregate vol (controls/known families)
    "VIX","VIX3M","VIX6M","VIX9D","VXV","VXMT","VXST","VXZ","SKEW","GVZ","OVX","RVX",
]

def probe(sym, timeout=25):
    url = BASE % sym
    req = urllib.request.Request(url)
    req.add_header("User-Agent", UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            b = r.read()
        return dict(sym=sym, url=url, status=r.status, n_bytes=len(b),
                    head=b[:90].decode("utf-8", "replace"), ok=True, error=None)
    except urllib.error.HTTPError as e:
        return dict(sym=sym, url=url, status=e.code, n_bytes=0, head="",
                    ok=False, error="HTTPError %d" % e.code)
    except Exception as e:
        return dict(sym=sym, url=url, status=None, n_bytes=0, head="",
                    ok=False, error="%s: %s" % (type(e).__name__, e))

def main():
    out = []
    ctl = probe(CONTROL)
    print("CONTROL %s -> HTTP %s %dB" % (CONTROL, ctl["status"], ctl["n_bytes"]))
    assert ctl["ok"], "network path dead: control failed, all candidate results void"
    out.append(ctl)
    for s in CANDIDATES:
        r = probe(s)
        out.append(r)
        tag = "OK  " if r["ok"] else ("x%d " % r["status"] if r["status"] else "ERR ")
        print("%s %-8s %9s  %s" % (tag, r["sym"], r["n_bytes"], (r["error"] or r["head"][:60]).replace("\n", "|")))
        time.sleep(0.15)
    with open(__file__.replace(".py", "_out.json"), "w") as f:
        json.dump(out, f, indent=1)
    ok = [r["sym"] for r in out if r["ok"] and r["sym"] != CONTROL]
    print("\nSUMMARY: %d candidates probed, %d HTTP 200 -> %s" % (len(CANDIDATES), len(ok), ok))
    return 0

if __name__ == "__main__":
    sys.exit(main())
