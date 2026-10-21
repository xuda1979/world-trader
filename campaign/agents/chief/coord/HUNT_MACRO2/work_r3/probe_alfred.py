"""Charter 3(a) gate: probe ALFRED vintages availability with EXACT HTTP evidence.
No synthetic substitutes. If this fails for all 6 series -> STOP honestly."""
import json, os, sys, urllib.request, urllib.error, datetime as dt

KEY = None
for p in ("/Users/daxu/software/world-trader/.env.local", "/Users/daxu/software/world-trader/campaign/.env.local"):
    if os.path.exists(p):
        for line in open(p):
            if line.startswith("FRED_KEY="):
                KEY = line.strip().split("=", 1)[1]
                break
    if KEY: break
assert KEY, "FRED_KEY not found"
print("FRED_KEY: present (len=%d)" % len(KEY))

SERIES = ["PAYEMS", "UNRATE", "CPIAUCSL", "ICSA", "RSXFS", "IPMAN"]
out = {}
for sid in SERIES:
    # vintage probe: ALFRED realtime observations. Ask for a few release windows.
    url = ("https://api.stlouisfed.org/fred/series/observations"
           "?series_id=%s&api_key=%s&file_type=json"
           "&realtime_start=2010-01-01&realtime_end=2010-03-01"
           "&observation_start=2009-11-01&observation_end=2010-01-01" % (sid, KEY))
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            data = json.loads(r.read().decode())
        obs = data.get("observations", [])
        vintage_dates = sorted({o["date"] for o in obs if o.get("value") not in (".", None, "")})
        # count distinct realtime periods = vintages
        url2 = url.replace("realtime_end=2010-03-01", "realtime_end=2010-03-01")  # same
        out[sid] = {"http": "200", "n_obs": len(obs),
                    "obs_dates": len(vintage_dates),
                    "first": (obs[0]["date"], obs[0].get("realtime_start")) if obs else None,
                    "last": (obs[-1]["date"], obs[-1].get("realtime_start")) if obs else None,
                    "count_total": data.get("count"), "count_limit": data.get("limit")}
        print("%-9s HTTP200 n=%5d obs_dates=%3d realtime_start_first=%s" %
              (sid, len(obs), len(vintage_dates),
               obs[0].get("realtime_start") if obs else "NONE"))
    except urllib.error.HTTPError as e:
        out[sid] = {"http": "HTTP%d" % e.code, "body": e.read().decode()[:300]}
        print("%-9s HTTP%d BODY=%s" % (sid, e.code, out[sid]["body"]))
    except Exception as e:
        out[sid] = {"http": "ERR", "body": repr(e)[:200]}
        print("%-9s ERR %r" % (sid, e))

json.dump(out, open("/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_MACRO2/work_r3/probe_alfred_result.json", "w"), indent=1)
ok = [s for s in SERIES if out.get(s, {}).get("http") == "200" and out[s].get("n_obs", 0) > 0]
print("\nVIABLE SERIES: %d/6 -> %s" % (len(ok), ok))
