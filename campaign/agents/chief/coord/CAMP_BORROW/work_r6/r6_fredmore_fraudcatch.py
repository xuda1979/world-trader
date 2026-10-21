"""r6_fredmore_fraudcatch.py — CAMP_BORROW R6 charter (b): reproduce DATA_FREDMORE's
R5 verdicts from PUBLISHED artifacts + live FRED/ALFRED, with my OWN code (no import of
their verify_round5.py; I re-derive every claim). Also documents the concurrent
DATA_ORGANIZE destruction of tools/quant/data/alfred/<SID>/vintage.csv (14:10:22
2026-09-08) that their verifier now crashes on.

My reproduction targets (from coord/DATA_FREDMORE/FINDINGS.md ROUND 5):
  V1 level CSVs lint: DRALACBS n=166 1985-01-01..2026-04-01 gaps=0;
     DRCLACBS n=158 1987-01-01..2026-04-01 gaps=0; WPU05320104 n=511 1984-01-01..2026-07-01.
  V2 live equality: delivered values == live FRED, delivered end == live max obs
     (2026-04-01 / 2026-04-01 / 2026-07-01).
  V3 vintage: n=61/61/136 first-release blocks; lag floors >=130d DR pair, >=35d WPU;
     WPU coverage hole == exactly {2015-10-01}; DR pair holes == {}.
  V4 WPU break census from saved artifact wpu_full_history.json: 587 obs, 3 structure
     events (1983 dots), 9 disclosed >=30% market swings, first 1990-01 +95.8%, refuse=False.
  V5 DEAD_IDEAS: 2 DATA_FREDMORE-R5 rows, status data-acquired.
Exit 0 iff all checks pass.
"""
import csv, glob, json, os, subprocess, sys, datetime as dt

ROOT = "/Users/daxu/software/world-trader"
WORK = os.path.join(ROOT, "campaign/agents/chief/coord/CAMP_BORROW/work_r6")
MFRED = os.path.join(ROOT, "tools/quant/data/more_fred")
ALF = os.path.join(ROOT, "tools/quant/data/alfred")
sys.path.insert(0, MFRED)
sys.path.insert(0, ALF)
import alfred_dl  # noqa: E402  (their own shipped lib, public API only)

P, F = [], []


def check(name, cond, detail=""):
    (P if cond else F).append(name)
    print(("PASS " if cond else "FAIL ") + name + (" | " + str(detail) if detail and not cond else ""))


def key():
    for line in open(os.path.join(ROOT, ".env.local")):
        if line.startswith("FRED_KEY="):
            return line.strip().split("=", 1)[1]
    raise AssertionError("no FRED_KEY in .env.local")


def read_level(path):
    with open(path) as f:
        return [(r["date"], float(r["value"])) for r in csv.DictReader(f)]


def gaps(days, freq):
    want = {"monthly": 92, "quarterly": 200}[freq]
    g = 0
    for i in range(len(days) - 1):
        a, b = dt.date.fromisoformat(days[i]), dt.date.fromisoformat(days[i + 1])
        if (b - a).days > want:
            g += 1
    return g


# ---- V1: level CSV lint from disk (recomputed, their numbers pinned) -----------
LV = {"DRALACBS": (166, "1985-01-01", "2026-04-01", "quarterly"),
      "DRCLACBS": (158, "1987-01-01", "2026-01-01", "quarterly"),
      "WPU05320104": (511, "1984-01-01", "2026-07-01", "monthly")}
# NOTE: DRCLACBS end pinned from THEIR findings text ("1987-01-01..2026-04-01"); I use
# 2026-04-01 below via the table (kept the dict honest by re-checking against their text).
LV["DRCLACBS"] = (158, "1987-01-01", "2026-04-01", "quarterly")

for sid, (n, start, end, freq) in LV.items():
    p = os.path.join(MFRED, f"{sid}.csv")
    ok = os.path.exists(p)
    check(f"V1 {sid} exists", ok)
    if not ok:
        continue
    rows = read_level(p)
    days = [d for d, _ in rows]
    vals = [v for _, v in rows]
    check(f"V1 {sid} n=={n} start=={start} end=={end}",
          len(rows) == n and days[0] == start and days[-1] == end,
          f"n={len(rows)} {days[0]}..{days[-1]}")
    check(f"V1 {sid} gaps==0 ordered no-dot",
          gaps(days, freq) == 0
          and all(days[i] < days[i + 1] for i in range(len(days) - 1))
          and all(v == v and abs(v) != float("inf") for v in vals))

# ---- V2: live equality vs FRED -------------------------------------------------
def live_series(sid):
    url = ("https://api.stlouisfed.org/fred/series/observations?series_id=%s&api_key=%s"
           "&file_type=json&observation_start=%s&observation_end=%s"
           % (sid, key(), LV[sid][1], LV[sid][2]))
    import urllib.request
    with urllib.request.urlopen(url, timeout=60) as r:
        obs = json.loads(r.read().decode())["observations"]
    return [(o["date"], float(o["value"])) for o in obs if o["value"] != "."]


import urllib.request  # noqa: E402
for sid in LV:
    got = read_level(os.path.join(MFRED, f"{sid}.csv"))
    liv = live_series(sid)
    same = len(got) == len(liv) and all(
        a[0] == b[0] and abs(a[1] - b[1]) <= 5e-9 * max(1.0, abs(b[1]))
        for a, b in zip(got, liv))
    check(f"V2 {sid} delivered==live n={len(liv)}", same, f"delivered n={len(got)} live n={len(liv)}")

# ---- V3: vintage reproduction from LIVE ALFRED (files were deleted at 14:10) ---
OUTD = os.path.join(WORK, "vintage_rebuilt")
os.makedirs(OUTD, exist_ok=True)
VC = {"DRALACBS": 61, "DRCLACBS": 61, "WPU05320104": 136}
FLOORS = {"DRALACBS": 130, "DRCLACBS": 130, "WPU05320104": 35}
HOLES = {"DRALACBS": set(), "DRCLACBS": set(), "WPU05320104": {"2015-10-01"}}
vres = {}
for sid, want_n in VC.items():
    (vrows, nmiss), verr = alfred_dl.fetch_first_release(sid, key())
    check(f"V3 {sid} live fetch ok", verr is None, verr)
    if verr:
        continue
    lags = [(dt.date.fromisoformat(a) - dt.date.fromisoformat(b)).days for a, b, _ in vrows]
    ordered = all((vrows[i][0], vrows[i][1]) < (vrows[i + 1][0], vrows[i + 1][1])
                  for i in range(len(vrows) - 1))
    # coverage holes: POST-BIRTH only (ALFRED first-release log starts at series birth;
    # pre-birth level rows are not expected to have first-release blocks)
    obs_set = set(b for _, b, _ in vrows)
    birth = min(obs_set)
    lvl = read_level(os.path.join(MFRED, f"{sid}.csv"))
    tail = set(d for d, _ in lvl if d >= birth)
    holes = sorted(tail - obs_set)
    check(f"V3 {sid} vintage n=={want_n}", len(vrows) == want_n, f"n={len(vrows)} err={verr}")
    check(f"V3 {sid} lag_min>=floor({FLOORS[sid]}) (got min {min(lags)})", min(lags) >= FLOORS[sid])
    check(f"V3 {sid} ordered", ordered)
    check(f"V3 {sid} coverage holes == {sorted(HOLES[sid])}",
          set(holes) == HOLES[sid], f"holes={holes}")
    # save rebuilt vintage (restore evidence; original format preserved)
    alfred_dl.write_vintage_csv(os.path.join(OUTD, sid, "vintage.csv"), vrows)
    vres[sid] = {"n": len(vrows), "lag_min": min(lags), "lag_max": max(lags), "err": None}

# ---- V4: WPU break census from their SAVED artifact -----------------------------
# The artifact is a flat list of (date, value); the 1983 suppressed obs are ABSENT
# monthly slots (the '.' values never made it into the saved JSON), so I re-derive
# the structure events INDEPENDENTLY as absent grid slots on a monthly calendar.
art = json.load(open("/Users/daxu/software/world-trader/campaign/agents/chief/coord/DATA_FREDMORE/work_r5/wpu_full_history.json"))
check("V4 artifact is flat list n==587", isinstance(art, list) and len(art) == 587, len(art))
alld = [d for d, _ in art]
vals = [float(v) for _, v in art]


def absent_slots(days, freq):
    """Independently re-derive structure events: grid slots with no row."""
    out = set()
    if freq == "monthly":
        cur = dt.date(1977, 6, 1)
        seen = set(days)
        while cur <= dt.date(2026, 7, 1):
            iso = cur.isoformat()[:8] + "01"
            if iso not in seen:
                out.add(iso)
            y, m = cur.year, cur.month + 1
            if m == 13:
                cur = dt.date(cur.year + 1, 1, 1)
            else:
                cur = dt.date(cur.year, m, 1)
    return out


events = absent_slots(alld, "monthly")
check("V4 absent-grid-slot structure events == exactly 1983-04/08/12",
      events == {"1983-04-01", "1983-08-01", "1983-12-01"}, sorted(events))
swings = []
for i in range(1, len(alld)):
    chg = (vals[i] - vals[i - 1]) / vals[i - 1] * 100.0
    if abs(chg) >= 30.0:
        swings.append((alld[i], chg))
check("V4 disclosed swings==9", len(swings) == 9, [(d, round(c, 1)) for d, c in swings])
check("V4 first swing 1990-01 +95.8%", swings and swings[0][0].startswith("1990-01")
      and abs(swings[0][1] - 95.8) < 0.15, swings[:1])
check("V4 no swing coincides with a structure event",
      not any(d in events for d, _ in swings))
# refuse gate: values continuous across the 1983 interlude within 30%
pre = [(d, v) for d, v in zip(alld, vals) if d < "1983-04-01"][-1]
post = [(d, v) for d, v in zip(alld, vals) if d > "1983-12-01"][0]
check("V4 interlude continuous within 30% (refuse=False)",
      abs(post[1] - pre[1]) / pre[1] < 0.30, f"pre={pre} post={post}")

# ---- V5: DEAD_IDEAS rows --------------------------------------------------------
rows = list(csv.DictReader(open(os.path.join(ROOT, "campaign/results/DEAD_IDEAS.csv"))))
frows = [r for r in rows if r["source"].strip() == "DATA_FREDMORE-R5"]
check("V5 DEAD_IDEAS DATA_FREDMORE-R5 rows==2", len(frows) == 2, len(frows))
check("V5 both status=data-acquired",
      all(r["status"].strip() == "data-acquired" for r in frows))
check("V5 DRALACBS + WPU05320104 named",
      any("DRALACBS" in r["evidence"] for r in frows)
      and any("WPU05320104" in r["evidence"] for r in frows))
check("V5 DEAD_IDEAS dynamic count sane (>=142 at R6 start, no dup ideas)",
      len(rows) >= 142 and len(set(r["idea"] for r in rows)) == len(rows),
      f"n={len(rows)} dups={len(rows)-len(set(r['idea'] for r in rows))}")

# ---- summary ---------------------------------------------------------------------
print("\nREPRODUCED: %d PASS / %d FAIL" % (len(P), len(F)))
if F:
    print("FAILURES:")
    for name in F:
        print("  -", name)
with open(os.path.join(WORK, "r6_fredmore_repro_scorecard.json"), "w") as f:
    json.dump({"pass": len(P), "fail": len(F), "failures": F,
               "vintage_rebuilt": vres,
               "note": "alfred/<SID>/vintage.csv destroyed by concurrent DATA_ORGANIZE "
                       "session ~14:10:22 2026-09-08; rebuilt from live ALFRED into "
                       "work_r6/vintage_rebuilt/ — see FINDINGS ROUND 6"},
              f, indent=1)
sys.exit(1 if F else 0)
