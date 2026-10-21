"""R5 energy-corner id discovery via FRED /series/search (no more guessing)."""
import json, os, urllib.request, urllib.error

ROOT = "/Users/daxu/software/world-trader"
KEY = [l.strip().split("=",1)[1] for l in open(os.path.join(ROOT,".env.local")) if l.startswith("FRED_KEY=")][0]
BASE = "https://api.stlouisfed.org/fred"

def search(text, limit=25):
    url = f"{BASE}/series/search?search_text={urllib.request.quote(text)}&api_key={KEY}&file_type=json&search_type=full_text&limit={limit}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read().decode()).get("seriess", []), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP{e.code}"

for text in ("propane", "butane", "natural gas liquids", "liquefied petroleum gases"):
    ss, err = search(text)
    print(f"\n=== search '{text}': {err or len(ss)} results")
    for s in ss or []:
        sid = s["id"]
        if s["frequency_short"] in ("D","W","M") and not any(k in sid for k in ("NME","XMKT")):
            print(f"  {sid:18s} {s['frequency_short']} {s['observation_start']}..{s['observation_end']}  {s['title'][:80]}")
