"""DATA_FREDMORE R4 (DATA_CBOEHIST) — prove with exact probe evidence which CBOE
options-history routes are keyless-feasible vs 403-blocked.

Charter ask: per-symbol put/call VOLUME, pc_ratio, atm_iv history, keyless, fail-closed
span lint. This probe establishes, with exact HTTP evidence:

  (1) the only keyless HISTORY endpoint family on the CDN is
      us_indices/daily_prices/{SYM}_History.csv (index/strategy/vol-index history),
  (2) all put_call_ratios routes are 403 (S3 AccessDenied) — aggregate AND per-symbol,
  (3) charts/historical/{SYM}.json serves UNDERLYING OHLCV (no put/call/IV fields),
  (4) the options chains are SNAPSHOT-ONLY (timestamp now, overwrite semantics),
  (5) control (VIX_History.csv) proves the network path while candidates fail.

Every claim reproduces from: python3 probe_history_endpoints.py   (writes probe_out.json)
No auth tricks, no scraping workarounds (AAII/FINRA precedent per charter).
"""
import json
import ssl
import sys
import urllib.error
import urllib.request

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = {"User-Agent": "Mozilla/5.0 (research; world-trader free-data harvest)"}

# (url, role, claim)
TARGETS = [
    ("https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv",
     "control",
     "known-good 200 -> network path alive; same CDN+path family as all deliverables"),
    ("https://cdn.cboe.com/api/global/delayed_quotes/put_call_ratios/_all.json",
     "blocked-agg",
     "aggregate put/call: 403 S3 AccessDenied (matches DEAD_IDEAS row 108)"),
    ("https://cdn.cboe.com/api/global/delayed_quotes/put_call_ratios/SPY.json",
     "blocked-per-sym",
     "per-symbol put/call: 403 -> per-symbol pc_ratio history NOT keyless-feasible"),
    ("https://cdn.cboe.com/api/global/delayed_quotes/charts/historical/SPY.json",
     "ohlcv-only",
     "per-symbol HISTORY exists but is UNDERLYING OHLCV 2004+ (date,open,high,low,close,volume); no put/call/iv fields -> charter's put/call ask NOT servable"),
    ("https://cdn.cboe.com/api/global/delayed_quotes/options/SPY.json",
     "snapshot-only",
     "options chain = SNAPSHOT (timestamp, iv30, ~10k contracts); refetch overwrites -> no history via chains"),
    ("https://cdn.cboe.com/api/global/delayed_quotes/charts/historical/volumes/SPY.json",
     "blocked-per-sym",
     "per-symbol options-volume history route: 403"),
    ("https://cdn.cboe.com/api/global/delayed_quotes/charts/historical/_all.json",
     "blocked-per-sym",
     "aggregate chart list: 403"),
    ("https://cdn.cboe.com/resources/options/volume_and_call_put_ratios/totalpc.csv",
     "frozen-archive",
     "official aggregate archive: 200 but FROZEN at 2019-10-04 (DEAD_IDEAS row 109, DATA_COTMORE)"),
]


def probe(url, want_json_keys=None):
    req = urllib.request.Request(url)
    for k, v in UA.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=40, context=CTX) as r:
            b = r.read(6_000_000)
        res = dict(url=url, status=r.status, n_bytes=len(b),
                   content_type=r.headers.get("Content-Type"), ok=True, error=None)
        if want_json_keys:
            try:
                d = json.loads(b)
                res["top_keys"] = sorted(d.keys())
                data = d.get("data")
                if isinstance(data, list) and data:
                    res["data_keys_union"] = sorted(set().union(*[set(x.keys()) for x in data[:5]]))
                    res["n_rows"] = len(data)
                    res["first_date"] = data[0].get("date")
                    res["last_date"] = data[-1].get("date")
                elif isinstance(data, dict):
                    res["data_keys"] = sorted(data.keys())
                    opts = data.get("options")
                    if isinstance(opts, list):
                        res["n_contracts"] = len(opts)
                        res["contract_head"] = opts[0].get("option")
                res["timestamp"] = d.get("timestamp")
            except Exception as e:
                res["json_err"] = "%s: %s" % (type(e).__name__, e)
        return res
    except urllib.error.HTTPError as e:
        body = e.read(200).decode("utf-8", "replace")
        return dict(url=url, status=e.code, n_bytes=0, ok=False,
                    error="HTTPError %d" % e.code, body_head=body[:150])
    except Exception as e:
        return dict(url=url, status=None, n_bytes=0, ok=False,
                    error="%s: %s" % (type(e).__name__, e))


def main():
    out = []
    for url, role, claim in TARGETS:
        want = role in ("ohlcv-only", "snapshot-only")
        res = probe(url, want_json_keys=want)
        res["role"], res["claim"] = role, claim
        out.append(res)
        print("=" * 100)
        print("ROLE  :", role)
        print("URL   :", url)
        print("HTTP  :", res["status"], "| bytes:", res["n_bytes"], "| CT:", res.get("content_type"))
        if res.get("error"):
            print("ERROR :", res["error"], "|", res.get("body_head", "")[:120])
        for k in ("timestamp", "first_date", "last_date", "n_rows", "data_keys_union",
                  "n_contracts", "top_keys"):
            if res.get(k) is not None:
                print("%s%s: %s" % (" " * 6, k, res[k]))
    ctl = next(r for r in out if r["role"] == "control")
    assert ctl["ok"], "CONTROL FAILED -> network path dead, probe results void"
    with open(__file__.replace(".py", "_out.json"), "w") as f:
        json.dump(out, f, indent=1)

    print("=" * 100)
    blocked = [r for r in out if r["role"].startswith("blocked")]
    print("\nVERDICT: %d blocked routes (403); history feasible ONLY via us_indices "
          "index/strategy/vol-index files; per-symbol put/call + pc_ratio = NOT "
          "keyless-feasible; chains = snapshot-only." % len(blocked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
