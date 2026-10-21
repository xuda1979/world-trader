"""Round-3 pre-fetch reality probes (evidence for the TDD spec). 2026-09-07."""
import json, urllib.request, urllib.error

KEY = [l.split("=", 1)[1].strip() for l in open("/Users/daxu/software/world-trader/.env.local")
       if l.startswith("FRED_KEY")][0]
BASE = "https://api.stlouisfed.org/fred"

def get(path, series_id, **params):
    url = f"{BASE}/{path}?series_id={series_id}&api_key={KEY}&file_type=json"
    for k, v in params.items():
        url += f"&{k}={v}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode()[:200]

vd, err = get("series/vintagedates", "SP500")
print("SP500 vintagedates:", (str(vd)[:100] if vd else f"ERR {err}"))

vd2, err2 = get("series/vintagedates", "PAYEMS")
print("PAYEMS vintagedates n =", len(vd2.get("vintage_dates", [])), "first/last:",
      vd2["vintage_dates"][0], vd2["vintage_dates"][-1] if vd2 else err2)

ot, err = get("series/observations", "CPIAUCSL", output_type=4,
              realtime_start="2026-01-01", realtime_end="2026-09-07")
blocks = [o for o in ot["observations"] if o["date"] >= "2025-09-01"]
print("CPIAUCSL ot4 obs>=2025-09:", json.dumps(blocks))

for sid, obs in [("PAYEMS", "2020-03-01"), ("UNRATE", "2020-04-01"), ("ICSA", "2020-03-21")]:
    ot, err = get("series/observations", sid, output_type=4,
                  realtime_start="2020-03-01", realtime_end="2020-09-30")
    hit = [o for o in ot["observations"] if o["date"] == obs] if ot else f"ERR {err}"
    print(sid, obs, "->", hit[:2])
