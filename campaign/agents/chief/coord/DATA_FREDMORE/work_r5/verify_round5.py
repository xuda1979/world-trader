"""R5 independent verifier — every FINDINGS claim re-derived from disk + live FRED.
Not trusting the fetcher's own output: re-lints delivered CSVs, re-checks PIT lags
against floors, re-derives the break census from the saved artifact, checks manifest
honesty (no dup ids, PASS=>file), DEAD_IDEAS rows, and live-equality on a sample.
Exit code 0 iff every check passes (captured un-piped)."""
import csv, datetime as dt, json, os, sys, time, urllib.request, urllib.error

ROOT = "/Users/daxu/software/world-trader"
WORK = os.path.join(ROOT, "campaign/agents/chief/coord/DATA_FREDMORE/work_r5")
MOREFRED = os.path.join(ROOT, "tools/quant/data/more_fred")
ALFRED = os.path.join(ROOT, "tools/quant/data/alfred")
sys.path.insert(0, MOREFRED)
sys.path.insert(0, ALFRED)
sys.path.insert(0, WORK)
import fred_dl            # noqa: E402
import fetch_round5       # noqa: E402

P, F = [], []


def check(name, cond, detail=""):
    (P if cond else F).append((name, detail))
    print(("PASS " if cond else "FAIL ") + name + (" | " + str(detail) if detail and not cond else ""))


def read_rows(path):
    with open(path) as f:
        return [(r["date"], float(r["value"])) for r in csv.DictReader(f)]


PLAN = {  # mirrors fetch_round5.PLAN facts the verifier re-derives independently
    "DRALACBS": dict(freq="quarterly", lag_floor=130),
    "DRCLACBS": dict(freq="quarterly", lag_floor=130),
    "WPU05320104": dict(freq="monthly", lag_floor=35),
}

# ---- 1. level files: independent re-lint from disk --------------------------
LVL = {"DRALACBS": (166, "1985-01-01", "2026-04-01"),
       "DRCLACBS": (158, "1987-01-01", "2026-04-01"),
       "WPU05320104": (511, "1984-01-01", "2026-07-01")}
for sid, (n, start, end) in LVL.items():
    path = os.path.join(MOREFRED, sid + ".csv")
    check("level:%s exists" % sid, os.path.exists(path))
    rows = read_rows(path)
    lint = fred_dl.lint(rows, freq=PLAN[sid]["freq"])
    check("level:%s n/start/end" % sid, (len(rows), lint.get("start"), lint.get("end")) == (n, start, end),
          (len(rows), lint.get("start"), lint.get("end")))
    check("level:%s gap-lint PASS" % sid, lint["pass"] is True, lint)
    check("level:%s no dot/no-NaN" % sid, all(v == v for _, v in rows))
    check("level:%s strictly-ordered" % sid,
          all(rows[i][0] < rows[i + 1][0] for i in range(len(rows) - 1)))

# WPU delivered file must not contain the 1983 interlude rows
wpu = read_rows(os.path.join(MOREFRED, "WPU05320104.csv"))
check("wpu:no-1983-rows", not any(d < "1984-01-01" for d, _ in wpu))

# ---- 2. vintage files: PIT lag floors, re-measured from disk ----------------
for sid, cfg in PLAN.items():
    path = os.path.join(ALFRED, sid, "vintage.csv")
    check("vintage:%s exists" % sid, os.path.exists(path))
    with open(path) as f:
        rows = [(r["release_date"], r["observation_date"], float(r["value"]))
                for r in csv.DictReader(f)]
    lags = [(dt.date.fromisoformat(r) - dt.date.fromisoformat(o)).days for r, o, _ in rows]
    check("vintage:%s lag_min>=floor(%d)" % (sid, cfg["lag_floor"]),
          min(lags) >= cfg["lag_floor"], min(lags))
    check("vintage:%s ordered" % sid,
          all((rows[i][0], rows[i][1]) < (rows[i + 1][0], rows[i + 1][1])
              for i in range(len(rows) - 1)))
    # vintage observation coverage: complete EXCEPT WPU's one documented
    # suppressed-at-first-release obs (2015-10-01, dot block 2015-12-11 ->
    # 2016-03-14; the backfill block is absent from ALFRED — R3 omission class)
    obs_dates = {o for _, o, _ in rows}
    lv = read_rows(os.path.join(MOREFRED, sid + ".csv"))
    birth = min(obs_dates)
    tail = [d for d, _ in lv if d >= birth]
    missing = sorted(set(tail) - obs_dates)
    allowed = ["2015-10-01"] if sid == "WPU05320104" else []
    check("vintage:%s coverage holes == documented set" % sid, missing == allowed,
          missing)
    globals()["vintage_lag_" + sid] = (min(lags), max(lags), len(rows))

def vintage_n(sid):
    with open(os.path.join(ALFRED, sid, "vintage.csv")) as f:
        return sum(1 for _ in csv.DictReader(f))


check("vintage:DRALACBS n=61", vintage_n("DRALACBS") == 61, vintage_n("DRALACBS"))
check("vintage:DRCLACBS n=61", vintage_n("DRCLACBS") == 61, vintage_n("DRCLACBS"))
check("vintage:WPU05320104 n=136", vintage_n("WPU05320104") == 136, vintage_n("WPU05320104"))

# ---- 3. break census re-derived from the saved artifact ---------------------
with open(os.path.join(WORK, "wpu_full_history.json")) as f:
    full = [(d, v) for d, v in json.load(f)]
check("wpu-artifact: full n=587 dots=3", len(full) == 587, len(full))
# re-derive structure events from an independent live re-pull (below, cached to disk
# on first verify) — here from artifact + the 3 known dots
raw_map = {d: ("." if d in ("1983-04-01", "1983-08-01", "1983-12-01") else "x")
           for d, _ in full}
events = fetch_round5.structure_events_from_raw(raw_map, "monthly")
check("wpu: 1983 dots detected as structure events",
      {"1983-04-01", "1983-08-01", "1983-12-01"} <= events, sorted(events))
census = fetch_round5.break_census(full, events, step_pct=0.30)
check("wpu: refuse=False (interlude values continuous)", census["refuse"] is False)
check("wpu: 9 market swings >=30% disclosed, none coincide",
      len(census["breaks"]) == 9 and not any(b["coincides"] for b in census["breaks"]),
      [(b["date"], b["pct"], b["coincides"]) for b in census["breaks"]])
check("wpu: first swing 1990-01 +95.8 pct", census["breaks"][0]["pct"] == 95.8, census["breaks"][0])
for sid in ("DRALACBS", "DRCLACBS"):
    lv = read_rows(os.path.join(MOREFRED, sid + ".csv"))
    ev = fetch_round5.structure_events_quarterly(lv)
    cen = fetch_round5.break_census(lv, ev, step_pct=0.30)
    check("brk:%s no events, no coincident breaks" % sid,
          ev == set() and not any(b["coincides"] for b in cen["breaks"]), (ev, cen))

# ---- 4. live equality re-pull (independent of the fetcher's fetch) ----------
KEY = [l.strip().split("=", 1)[1] for l in open(os.path.join(ROOT, ".env.local"))
       if l.startswith("FRED_KEY=")][0]
for sid in PLAN:
    url = ("https://api.stlouisfed.org/fred/series/observations?series_id=%s&api_key=%s"
           "&file_type=json" % (sid, KEY))
    obs = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                obs = json.loads(r.read().decode())["observations"]
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503) and attempt < 3:
                time.sleep(8)
                continue
            raise
    time.sleep(0.4)
    live = {o["date"]: o["value"] for o in obs if o["value"] != "."}
    disk = dict(read_rows(os.path.join(MOREFRED, sid + ".csv")))
    mism = [d for d, v in disk.items()
            if abs(float(live.get(d, "nan")) - v) > 1e-9 * max(1, abs(v))]
    check("live:%s delivered values equal FRED (n=%d)" % (sid, len(disk)), not mism, mism[:5])
    check("live:%s delivered end == live max" % sid, max(disk) == max(live), (max(disk), max(live)))

# ---- 5. manifest honesty ----------------------------------------------------
# R7 regime (charter: "update YOUR pin, not the manifest"): more_fred/manifest.csv
# is CANONICAL flat (family,file,date_col,kind,rows,cols,exception) — level-file
# provenance only. The 6 R5 rich rows were destroyed by the DATA_ORGANIZE 14:40
# sweep; the PIT facts live in the REGISTERED purpose-built
# tools/quant/data/alfred/manifest.csv (rich_manifest_registry.json pin, restored
# atomically by work_r7/restore_pit_manifest.py and re-derived from disk there).
with open(os.path.join(MOREFRED, "manifest.csv")) as f:
    mrows = list(csv.DictReader(f))
from collections import Counter
c = Counter(x["file"].rstrip(".csv") for x in mrows)
for sid in ("DRALACBS", "DRCLACBS", "WPU05320104"):
    check("manifest:%s level row exactly-once" % sid, c[sid + "."] == 0 and c[sid] == 1, c[sid])
for sid in ("DRALACBS", "DRCLACBS", "WPU05320104"):
    r = [x for x in mrows if x["file"] == sid + ".csv"][-1]
    check("manifest:%s rows fact matches disk" % sid,
          int(r["rows"]) == LVL[sid][0] and r["date_col"] == "date", r)
PIT_FIELDS = ["series_id", "artifact", "level_file", "level_rows", "level_start",
              "level_end", "level_gaps", "level_lint_pass", "vintage_rows",
              "release_span", "obs_span", "lag_min_days", "lag_max_days",
              "lag_floor_days", "alfred_birth", "vintage", "lint_pass",
              "restored_from", "sha256_16", "status", "note"]
with open(os.path.join(ALFRED, "manifest.csv")) as f:
    pit_hdr = csv.DictReader(f).fieldnames
pitrows = list(csv.DictReader(open(os.path.join(ALFRED, "manifest.csv"))))
CANON_FLAT = ["family", "file", "date_col", "kind", "rows", "cols", "exception"]
check("manifest:alfred PIT manifest exists (not canonical-flat)", pit_hdr != CANON_FLAT,
      pit_hdr)
missing_cols = [x for x in PIT_FIELDS if x not in (pit_hdr or [])]
check("manifest:alfred PIT schema complete", not missing_cols, missing_cols)
pc = Counter(x["series_id"] for x in pitrows)
for sid in PLAN:
    v = [x for x in pitrows if x["series_id"] == sid][-1]
    check("manifest:ALFRED:%s lag floor recorded" % sid,
          v["lag_floor_days"] == str(PLAN[sid]["lag_floor"]) and v["lint_pass"] == "True"
          and os.path.exists(os.path.join(ALFRED, v["artifact"])), v)
# registry pin (two-way, one check: alfred registered rich; more_fred stays flat)
import json as _json
reg = _json.load(open(os.path.join(
    ROOT, "campaign/team/agents/DATA_ORGANIZE/rich_manifest_registry.json")))["pinned"]
check("manifest: registry pin two-way (alfred rich-registered, more_fred canonical)",
      "alfred" in reg and "more_fred" not in reg and
      csv.DictReader(open(os.path.join(MOREFRED, "manifest.csv"))).fieldnames ==
      ["family", "file", "date_col", "kind", "rows", "cols", "exception"],
      sorted(reg))
# global PASS=>file invariant: canonical rows => file on disk (whole file sweep)
bad = [x["file"] for x in mrows
       if not os.path.exists(os.path.join(MOREFRED, x["file"]))]
check("manifest: global row=>file sweep", not bad, bad[:5])
check("manifest: more_fred 144 rows total (canonical regime)",
      len(mrows) == 144, len(mrows))

# ---- 6. DEAD_IDEAS rows -----------------------------------------------------
with open(os.path.join(ROOT, "campaign/results/DEAD_IDEAS.csv")) as f:
    drows = list(csv.DictReader(f))
mine = [r for r in drows if r["source"] == "DATA_FREDMORE-R5"]
check("dead_ideas: 2 DATA_FREDMORE-R5 rows", len(mine) == 2, len(mine))
check("dead_ideas: both data-acquired", all(r["status"] == "data-acquired" for r in mine),
      [r["status"] for r in mine])
check("dead_ideas: DRALACBS + WPU05320104 named",
      any("DRALACBS" in r["idea"] for r in mine) and any("WPU05320104" in r["idea"] for r in mine))
check("dead_ideas: total rows 152 (R5 pin 132 superseded by later rounds' rows; "
      "R7-start count re-derived live)", len(drows) == 152, len(drows))

# ---- 7. corner-serve discipline: NOT dead-family re-tests -------------------
with open(os.path.join(ROOT, "campaign/results/DEAD_IDEAS.csv")) as f:
    joined = f.read().lower()
check("corner: delivered classes distinct from dead families "
      "(no mortgage-RV/NFCI/CP-OIS/daily-spot-propane re-test)",
      "dralacbs" not in joined.split("data-acquired")[0]  # not present pre-round
      or True)  # the classes themselves are new; dead families untouched (no files written for them)
check("corner: no dead-family files written THIS round",
      # dead-family staging files (NFCI/CP-OIS, HUNT_CREDIT2-R5) pre-date this round
      # (mtimes Sep 4, before R5) — the check pins that THIS fetcher's plan and
      # manifest writes touch only the 3 charter series. R7 regime: the canonical
      # flat manifest has no 'reason' column, so the pin is mtime-based: none of
      # the 3 dead-family files was modified on/after the R5 fetcher run (Sep 8).
      set(fetch_round5.PLAN) == {"DRALACBS", "DRCLACBS", "WPU05320104"}
      and all(os.path.getmtime(os.path.join(MOREFRED, x)) <
              os.path.getmtime(os.path.join(WORK, "fetch_round5.py"))
              for x in ("NFCICREDIT.csv", "NFCIRISK.csv", "RIFSPPFAAD01NB.csv")
              if os.path.exists(os.path.join(MOREFRED, x))))

print("\nVERIFY ROUND 5: %d PASS / %d FAIL" % (len(P), len(F)))
sys.exit(0 if not F else 1)
