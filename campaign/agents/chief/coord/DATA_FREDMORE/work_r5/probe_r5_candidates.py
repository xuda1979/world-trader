"""R5 candidate probe: live FRED API existence/span/metadata for credit+energy corners.
Control-first. Saves JSON, prints evidence. Exit 0 only if control + >=2 candidates alive."""
import json, os, sys, time, urllib.request, urllib.error, datetime as dt

ROOT = "/Users/daxu/software/world-trader"
KEY = None
with open(os.path.join(ROOT, ".env.local")) as f:
    for line in f:
        if line.startswith("FRED_KEY="):
            KEY = line.strip().split("=", 1)[1]
assert KEY, "no FRED_KEY in .env.local"

BASE = "https://api.stlouisfed.org/fred"

def get(path, params):
    url = f"{BASE}/{path}?series_id={params}&api_key={KEY}&file_type=json"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP{e.code}"
    except Exception as e:
        return None, repr(e)[:120]

out = {"probed_at": str(dt.datetime.now()), "control": {}, "candidates": {}}

# control: a series we KNOW exists and is in our manifest (CPIAUCSL)
meta, err = get("series", "CPIAUCSL")
out["control"] = {"series": "CPIAUCSL", "ok": meta is not None, "err": err}
print("control CPIAUCSL:", "OK" if meta else f"FAIL {err}")

CANDS = [
    # credit corner (HUNT_CREDIT2): SLOOS nets = bank lending STANDARDS class (new vs price spreads)
    ("DRCLACBS",   "credit"),   # net % tightening C&I standards large+middle firms
    ("DRCCLMACBS", "credit"),   # net % tightening credit-card standards
    ("DRALACBS",   "credit"),   # net % tightening consumer auto standards
    ("DRTSCILM",   "credit"),   # SLOOS terms large firms (verify exact meaning via notes)
    # propane-adjacent energy (HUNT_CMDT2)
    ("DPBUTANEBTX",   "energy"),  # Mont Belvieu TX butane daily spot
    ("WPU17511301",   "energy"),  # PPI by industry natural gas liquids (verify)
    ("WPU17511302",   "energy"),  # sibling code (verify)
    ("NOSLBBEM",      "energy"),  # (verify existence)
]
for sid, corner in CANDS:
    m, e1 = get("series", sid)
    time.sleep(0.4)
    row = {"corner": corner, "meta_ok": m is not None, "meta_err": e1}
    if m and m.get("seriess"):
        s = m["seriess"][0]
        row.update({k: s.get(k) for k in ("title", "observation_start", "observation_end",
                                          "frequency", "seasonal_adjustment", "last_updated", "notes")})
        row["notes"] = (row["notes"] or "")[:400]
        v, e2 = get("series/observations", sid + "&limit=1&sort_order=desc")
        time.sleep(0.4)
        row["obs_ok"] = v is not None
        row["obs_err"] = e2
        if v:
            obs = v.get("observations", [])
            row["latest_obs"] = obs[0]["date"] if obs else None
            row["latest_val"] = obs[0]["value"] if obs else None
    out["candidates"][sid] = row
    alive = row.get("meta_ok") and row.get("obs_ok")
    print(f"{sid:12s} {'ALIVE' if alive else 'DEAD/'+str(row.get('meta_err') or row.get('obs_err')):9s} "
          f"start={row.get('observation_start')} end={row.get('observation_end')} freq={str(row.get('frequency'))[:22]}")

# ALFRED vintagedates probe for the SLOOS credit candidates (PIT-lint source)
for sid in ("DRCLACBS", "DRCCLMACBS", "DRALACBS"):
    v, e = get("series/vintagedates", sid)
    time.sleep(0.4)
    n = len(v.get("vintage_dates", [])) if v else 0
    out["candidates"].setdefault(sid, {})["alfred_vintagedates"] = n
    out["candidates"][sid]["alfred_err"] = e
    print(f"{sid}: ALFRED vintagedates n={n} {e or ''}")

with open("probe_r5_candidates_out.json", "w") as f:
    json.dump(out, f, indent=1)
alive = [s for s, r in out["candidates"].items() if r.get("meta_ok")]
sys.exit(0 if (out["control"]["ok"] and len(alive) >= 2) else 1)
