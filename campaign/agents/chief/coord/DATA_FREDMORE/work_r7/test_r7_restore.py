"""DATA_FREDMORE R7 charter (a): PIT-manifest restoration tests — TDD RED-first.

Pins the post-restoration state after the DATA_ORGANIZE 14:40 crash destroyed the
6 R5 rich manifest rows (3 level provenance + 3 ALFRED PIT vintage rows with
lag_days) when it flattened more_fred/manifest.csv to the canonical 7-col schema,
and left alfred/manifest.csv header-only.

Restoration design (coordinator-ratified arithmetic: "update YOUR pin, not the
manifest" — more_fred/manifest.csv stays canonical at 144 data rows):
  - tools/quant/data/alfred/manifest.csv becomes a REGISTERED purpose-built PIT
    manifest (rich_manifest_registry.json mechanism, DATA_ETF_MORE R7 post-mortem)
    holding the 3 vintage artifacts' PIT facts the flat schema cannot express.
  - organize_lib's regen guard must refuse to flatten it ever again.
  - verify_round5.py (my verifier) returns to 64 PASS / 0 FAIL.
  - verify_round6.py's C4 check becomes a same-date comparison (the R6 FINDINGS
    caveat: it compared cross-date while claiming "no revision at the boundary").
"""
import csv
import importlib.util
import json
import os
import subprocess
import sys

import pytest

REPO = "/Users/daxu/software/world-trader"
AG = f"{REPO}/campaign/agents/chief/coord/DATA_FREDMORE"
ALFRED = f"{REPO}/tools/quant/data/alfred"
MOREFRED = f"{REPO}/tools/quant/data/more_fred"
REG = f"{REPO}/campaign/team/agents/DATA_ORGANIZE/rich_manifest_registry.json"
CANON = ["family", "file", "date_col", "kind", "rows", "cols", "exception"]

# R5 charter pins (fetch_round5.PLAN / verify_round5 PLAN facts)
PLAN = {
    "DRALACBS": dict(level_rows=166, level_start="1985-01-01", level_end="2026-04-01",
                     lag_floor=130, alfred_birth="2011-05-24"),
    "DRCLACBS": dict(level_rows=158, level_start="1987-01-01", level_end="2026-04-01",
                     lag_floor=130, alfred_birth="2011-05-24"),
    "WPU05320104": dict(level_rows=511, level_start="1984-01-01", level_end="2026-07-01",
                        lag_floor=35, alfred_birth="2015-03-13"),
}
REQUIRED_PIT_COLS = [
    "series_id", "artifact", "level_file", "level_rows", "level_start", "level_end",
    "level_gaps", "level_lint_pass", "vintage_rows", "release_span", "obs_span",
    "lag_min_days", "lag_max_days", "lag_floor_days", "alfred_birth", "vintage",
    "lint_pass", "restored_from", "sha256_16", "status", "note",
]


def _load_lib():
    spec = importlib.util.spec_from_file_location(
        "organize_lib", f"{REPO}/campaign/team/agents/DATA_ORGANIZE/organize_lib.py")
    lib = importlib.util.module_from_spec(spec)
    sys.modules["organize_lib"] = lib
    spec.loader.exec_module(lib)
    return lib


def _rows(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def _header(path):
    with open(path, newline="") as fh:
        return csv.DictReader(fh).fieldnames


def _sha256_16(path):
    import hashlib
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


# --------------------------------------------- T1: alfred PIT manifest restored

def test_t1_alfred_pit_manifest_restored_with_all_pit_facts():
    rows = _rows(f"{ALFRED}/manifest.csv")
    assert len(rows) == 3, rows
    got = {r["series_id"]: r for r in rows}
    assert set(got) == set(PLAN), sorted(got)
    for sid, cfg in PLAN.items():
        r = got[sid]
        # every vintage-CSV fact re-derived from disk must match the row
        vpath = f"{ALFRED}/{sid}/vintage.csv"
        with open(vpath) as fh:
            vrows = [(x["release_date"], x["observation_date"])
                     for x in csv.DictReader(fh)]
        lags = [(__import__("datetime").date.fromisoformat(a)
                 - __import__("datetime").date.fromisoformat(b)).days
                for a, b in vrows]
        assert r["artifact"] == f"{sid}/vintage.csv", r
        assert r["vintage"] == "True" and r["lint_pass"] == "True", r
        assert r["status"] == "ok", r
        assert int(r["vintage_rows"]) == len(vrows), (sid, r["vintage_rows"], len(vrows))
        assert r["release_span"] == f"{vrows[0][0]}..{vrows[-1][0]}", r
        assert r["obs_span"] == f"{vrows[0][1]}..{vrows[-1][1]}", r
        assert int(r["lag_min_days"]) == min(lags) >= cfg["lag_floor"], (sid, min(lags))
        assert int(r["lag_max_days"]) == max(lags), (sid, max(lags))
        assert int(r["lag_floor_days"]) == cfg["lag_floor"], r
        assert r["alfred_birth"] == cfg["alfred_birth"], r
        # level-file facts
        lrows = _rows(f"{MOREFRED}/{sid}.csv")
        assert r["level_file"] == f"{sid}.csv"
        assert int(r["level_rows"]) == len(lrows) == cfg["level_rows"], (sid, len(lrows))
        assert r["level_start"] == lrows[0]["date"] == cfg["level_start"], r
        assert r["level_end"] == lrows[-1]["date"] == cfg["level_end"], r
        assert r["level_gaps"] == "0" and r["level_lint_pass"] == "True", r
        # provenance + byte pin
        assert "CAMP_BORROW/work_r6/vintage_rebuilt" in r["restored_from"], r
        assert r["sha256_16"] == _sha256_16(vpath), (sid, r["sha256_16"])


def test_t1b_pit_manifest_header_is_not_the_flat_canonical_schema():
    hdr = _header(f"{ALFRED}/manifest.csv")
    assert hdr != CANON, "PIT facts cannot live in the flat schema; header must be rich"
    for c in REQUIRED_PIT_COLS:
        assert c in hdr, c


# --------------------------------- T2: registry pin (two-way fail-closed grant)

def test_t2_registry_pins_alfred_family():
    reg = json.load(open(REG))["pinned"]
    assert "alfred" in reg, sorted(reg)
    pin = reg["alfred"]
    for c in REQUIRED_PIT_COLS:
        assert c in pin["required_cols"], c
    hdr = _header(f"{ALFRED}/manifest.csv")
    assert hdr != CANON, "registered family regaining the canonical schema must fail"
    assert not any(c not in hdr for c in pin["required_cols"])


# ------------------------------- T3: organize_lib regen guard holds post-restore

def test_t3_regen_guard_refuses_alfred_flatten():
    lib = _load_lib()
    with pytest.raises(lib.ManifestRegenerationRefused):
        lib.write_manifest("alfred")
    # and more_fred's canonical manifest is likewise guarded against silent regen
    # only if it were rich — it is canonical, so the guard must ALLOW it (no pin):
    reg = json.load(open(REG))["pinned"]
    assert "more_fred" not in reg, "more_fred stays canonical; must NOT be registered"


# ------------------------- T4: more_fred canonical manifest preserved (my pin)

def test_t4_more_fred_canonical_state_preserved():
    p = f"{MOREFRED}/manifest.csv"
    assert _header(p) == CANON
    rows = _rows(p)
    # 144 data rows + header = 145 lines (the coordinator's "145")
    assert len(rows) == 144, len(rows)
    disk = sorted(f for f in os.listdir(MOREFRED)
                  if f.endswith(".csv") and f != "manifest.csv")
    got = sorted(r["file"] for r in rows)
    assert got == disk, "file<->row bijection broken"
    for r in rows:
        assert r["date_col"] == "date" and r["kind"] == "timeseries", r
    # the 3 level files keep their R5 row counts in the flat rows/cols facts
    by_file = {r["file"]: r for r in rows}
    for sid, cfg in PLAN.items():
        assert int(by_file[f"{sid}.csv"]["rows"]) == cfg["level_rows"], sid


# ------------------------------- T5: my R5 verifier is back to 64 PASS / 0 FAIL

def test_t5_verify_round5_back_to_64_0():
    r = subprocess.run(
        [sys.executable, f"{AG}/work_r5/verify_round5.py"],
        capture_output=True, text=True, timeout=900, cwd=REPO)
    assert r.returncode == 0, (r.returncode, r.stdout[-2000:], r.stderr[-800:])
    assert "VERIFY ROUND 5: 64 PASS / 0 FAIL" in r.stdout, r.stdout[-500:]


# --------------------- T6: verify_round6 C4 is a same-date comparison, honestly

def test_t6_c4_check_is_same_date_not_cross_date():
    src = open(f"{AG}/work_r6/verify_round6.py").read()
    assert "C4. same-date" in src, "C4 label must state same-date semantics"
    assert "no revision at the boundary)\")" not in src.replace(
        "C4. same-date", ""), "old cross-date-overstating C4 label still present"
    # the comparison must be keyed on the on-disk last DATE against the live value
    # AT THAT DATE (a dict/lookup), not against live[-1] (a different date)
    import re
    c4 = src[src.index("C4."):src.index("C5.")]
    assert "live_by_date" in c4 or "live_map" in c4, c4


# ---------------- T7 (FREDMORE-R7 fix): notes are per-series and format-clean

def test_t7_manifest_notes_per_series_no_placeholder_no_cross_series_claim():
    rows = _rows(f"{ALFRED}/manifest.csv")
    got = {r["series_id"]: r for r in rows}
    hole_claim = "2015-10-01 suppressed-at-first-release coverage hole"
    for sid, r in got.items():
        # every lag floor is actually printed (no unformatted %d placeholder)
        assert "%d" not in r["note"] and "%s" not in r["note"], (sid, r["note"])
        assert str(PLAN[sid]["lag_floor"]) in r["note"], (sid, r["note"])
        # the WPU-only hole claim follows the disk fact: WPU obs SKIP 2015-10-01,
        # the DR quarterly series HAVE 2015-10-01 (verified against vintage.csv)
        with open(f"{ALFRED}/{sid}/vintage.csv") as fh:
            obs = {x["observation_date"] for x in csv.DictReader(fh)}
        has_1010 = "2015-10-01" in obs
        if sid == "WPU05320104":
            assert not has_1010, "WPU hole fact changed; note must be re-derived"
            assert hole_claim in r["note"], sid
        else:
            assert has_1010, (sid, "2015-10-01 present; hole claim would be false")
            assert hole_claim not in r["note"], (sid, "cross-series note contamination")
