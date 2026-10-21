"""R5 finalists: obs payload + ALFRED vintagedates + notes for PIT/BREAK lint design."""
import json, os, urllib.request, urllib.error

ROOT = "/Users/daxu/software/world-trader"
KEY = [l.strip().split("=",1)[1] for l in open(os.path.join(ROOT,".env.local")) if l.startswith("FRED_KEY=")][0]
BASE = "https://api.stlouisfed.org/fred"

def get(path):
    url = f"{BASE}/{path}&api_key={KEY}&file_type=json"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP{e.code}"

out = {}
for sid in ("DRCLACBS", "DRALACBS", "WPU05320104"):
    full, e1 = get(f"series/observations?series_id={sid}")
    vin, e2 = get(f"series/vintagedates?series_id={sid}")
    notes, e3 = get(f"series?series_id={sid}")
    row = {"obs_err": e1, "vin_err": e2, "notes_err": e3}
    if full:
        obs = full["observations"]
        row["n_obs"] = len(obs)
        row["first3"] = [(o["date"], o["value"]) for o in obs[:3]]
        row["last3"] = [(o["date"], o["value"]) for o in obs[-3:]]
        row["n_missing_dots"] = sum(1 for o in obs if o["value"] in (".", ""))
        # quarterly grid completeness
        dates = sorted(o["date"] for o in obs if o["value"] != ".")
        row["first_real"], row["last_real"] = dates[0], dates[-1]
    if vin:
        vd = vin.get("vintage_dates", [])
        row["n_vintagedates"] = len(vd)
        row["vintagedates_first5"] = vd[:5]
        row["vintagedates_last3"] = vd[-3:]
    if notes and notes.get("seriess"):
        s = notes["seriess"][0]
        row["title"] = s.get("title")
        row["notes_head"] = (s.get("notes") or "")[:600]
        row["last_updated"] = s.get("last_updated")
    out[sid] = row
    print(f"--- {sid}")
    for k in ("n_obs","n_missing_dots","first_real","last_real","n_vintagedates","obs_err","vin_err"):
        if k in row: print(f"  {k}: {row[k]}")
    print(f"  first3: {row.get('first3')}")
    print(f"  last3: {row.get('last3')}")
    print(f"  title: {row.get('title')}")

with open("probe_r5_finalists_out.json","w") as f:
    json.dump(out, f, indent=1)
