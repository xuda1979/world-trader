"""R5 tests (TDD, RED first): charter (a) 3 NEW FRED series for the R5 corners.

Corners served (charter R5 (a)):
  credit spreads for HUNT_CREDIT2  -> DRALACBS, DRCLACBS (bank delinquency rates,
     credit-QUALITY cycle; NOT the dead spread families of the HUNT_CREDIT2-R5 row:
     mortgage-spread RV / NFCI regime / CP-OIS stress)
  propane-adjacent energy for HUNT_CMDT2 -> WPU05320104 (PPI Propane monthly index,
     1977+; distinct object from the dead DPROPANEMBTX daily-spot families)

Lint = gap structure (fred_dl.lint) + PIT lag (alfred_dl.lint_vintage) +
source-transition BREAK gate (fetch_round5.break_census, DATA_COTMORE R4 pattern).

Measured reality pinned (live FRED probes 2026-09-08, see probe_r5_finalists_out.json):
  DRALACBS  n=166 1985-01-01..2026-04-01 quarterly 0 dots 0 absent slots; vintage
            blocks 61, ALFRED birth 2011-05-24, first-release lag 136..166d -> floor 130
  DRCLACBS  n=158 1987-01-01..2026-04-01 same class; 61 blocks, floor 130
  WPU05320104 587 real obs 1977-06..2026-07, 3 dots @1983-04/08/12 = quarterly-
            publication interlude -> head-trim to 1984-01-01 (no splice), trimmed n=511
            gaps=0; vintage blocks 137, birth 2015-03-13, lag 37..105d -> floor 35
"""
import csv, datetime as dt, os, sys

ROOT = "/Users/daxu/software/world-trader"
WORK = os.path.join(ROOT, "campaign/agents/chief/coord/DATA_FREDMORE/work_r5")
MOREFRED = os.path.join(ROOT, "tools/quant/data/more_fred")
ALFRED = os.path.join(ROOT, "tools/quant/data/alfred")
for p in (MOREFRED, os.path.join(ROOT, "tools/quant/data/alfred"), WORK):
    if p not in sys.path:
        sys.path.insert(0, p)

import fred_dl  # noqa: E402


def _read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def _rows(path):
    return [(r["date"], float(r["value"])) for r in _read_csv(path)]


# ---------------------------------------------------------------- fetch_round5
def test_fetch_round5_module_exists():
    import fetch_round5  # noqa: F401


def test_level_files_delivered_quarterly_lint_pass():
    got = {"DRALACBS": (166, "1985-01-01", "2026-04-01"),
           "DRCLACBS": (158, "1987-01-01", "2026-04-01")}
    for sid, (n, start, end) in got.items():
        rows = _rows(os.path.join(MOREFRED, sid + ".csv"))
        assert len(rows) == n, (sid, len(rows))
        lint = fred_dl.lint(rows, freq="quarterly")
        assert lint["pass"], (sid, lint)
        assert lint["start"] == start and lint["end"] == end, (sid, lint)
        assert lint["gaps"] == 0


def test_wpu_trimmed_monthly_lint_pass_no_1983_rows():
    rows = _rows(os.path.join(MOREFRED, "WPU05320104.csv"))
    assert len(rows) == 511, len(rows)
    lint = fred_dl.lint(rows, freq="monthly")
    assert lint["pass"], lint
    assert lint["start"] == "1984-01-01" and lint["end"] == "2026-07-01", lint
    assert lint["gaps"] == 0
    assert all(d >= "1984-01-01" for d, _ in rows)


# ---------------------------------------------------------------- vintage/PIT
def test_vintage_files_pit_lag_floors():
    import alfred_dl
    for sid, floor, min_n in (("DRALACBS", 130, 60), ("DRCLACBS", 130, 60),
                              ("WPU05320104", 35, 130)):
        path = os.path.join(ALFRED, sid, "vintage.csv")
        with open(path) as f:
            rdr = csv.DictReader(f)
            assert rdr.fieldnames == ["release_date", "observation_date", "value"], \
                (sid, rdr.fieldnames)
            rows = [(r["release_date"], r["observation_date"], float(r["value"]))
                    for r in rdr]
        assert len(rows) >= min_n, (sid, len(rows))
        v = alfred_dl.lint_vintage(rows, lag_floor=floor)
        assert v["pass"], (sid, floor, v)


def test_dr_series_have_2025q4_stamp_fed_not_bls():
    """The BLS family carries the 2025-10 shutdown hole; the Fed charge-off series
    must NOT (quarter stamped 2025-10-01 present). Pins cross-source discipline."""
    for sid in ("DRALACBS", "DRCLACBS"):
        dates = [d for d, _ in _rows(os.path.join(MOREFRED, sid + ".csv"))]
        assert "2025-10-01" in dates, sid


# ---------------------------------------------------------------- break gate
def test_wpu_vintage_only_coverage_hole_is_documented_suppressed_obs():
    """PIT honesty pin: obs 2015-10-01 was suppressed ('.') at first release
    (dot block 2015-12-11 -> 2016-03-14, live-verified 2026-09-08) and the
    backfilled value's ot4 block is absent from ALFRED (R3-documented FRED
    omission class). The vintage stream must therefore omit EXACTLY that one
    obs post-birth — no other coverage holes allowed."""
    import csv
    vpath = os.path.join(ALFRED, "WPU05320104", "vintage.csv")
    with open(vpath) as f:
        obs_dates = {r["observation_date"] for r in csv.DictReader(f)}
    lv = _rows(os.path.join(MOREFRED, "WPU05320104.csv"))
    birth = min(obs_dates)
    tail = [d for d, _ in lv if d >= birth]
    missing = sorted(set(tail) - obs_dates)
    assert missing == ["2015-10-01"], missing


def test_break_census_flags_step_adjacent_to_structure_event():
    import fetch_round5
    # synthetic: value halves across one MISSING slot (rename-stitch signature)
    rows = [("2020-01-01", 100.0), ("2020-02-01", 101.0), ("2020-03-01", 99.0),
            ("2020-05-01", 40.0), ("2020-06-01", 41.0)]  # 2020-04 absent
    structure = {"2020-04-01"}  # publication-structure event: absent slot
    out = fetch_round5.break_census(rows, structure_events=structure, step_pct=0.30)
    assert out["refuse"] is True, out
    assert any(b["date"] == "2020-05-01" and b["coincides"] for b in out["breaks"]), out


def test_break_census_market_step_without_structure_event_is_not_a_break():
    import fetch_round5
    # 45% move, no structure event anywhere: a market move, NOT a source break.
    # The census DISCLOSES the measured step (coincides=False) but never refuses.
    rows = [("2020-01-01", 100.0), ("2020-02-01", 145.0)]
    out = fetch_round5.break_census(rows, structure_events=set(), step_pct=0.30)
    assert out["refuse"] is False
    assert len(out["breaks"]) == 1 and out["breaks"][0]["coincides"] is False, out


def test_wpu_transition_recorded_but_delivered_span_clean():
    """1983 quarterly interlude = the publication-structure transition; it must be
    recorded with magnitudes while the delivered (head-trimmed) file is clean."""
    import fetch_round5, json
    # full history comes from the fetcher's saved evidence artifact
    with open(os.path.join(WORK, "wpu_full_history.json")) as f:
        full = [(d, v) for d, v in json.load(f)]
    # dots re-derived from the raw payload grid (absent-slot + dot detection)
    dates = {d for d, _ in full}
    structure = fetch_round5.structure_events_quarterly(full) | \
        {d for d in fetch_round5.structure_events_from_raw(
            {d: ("." if d not in dates else "x")
             for d in ("1983-04-01", "1983-08-01", "1983-12-01", "1984-01-01")})}
    assert {"1983-04-01", "1983-08-01", "1983-12-01"} <= structure, sorted(structure)
    out = fetch_round5.break_census(full, structure_events=structure, step_pct=0.30)
    # transition disclosed (dot cluster IS a structure event), no hard refuse:
    # the values across the interlude are continuous within 30%
    assert out["refuse"] is False, out
    assert not any(b["coincides"] for b in out["breaks"]), out
    # the DELIVERED file carries no 1983 rows
    delivered = _rows(os.path.join(MOREFRED, "WPU05320104.csv"))
    assert all(d >= "1984-01-01" for d, _ in delivered)


def test_dr_no_structure_events_no_breaks():
    import fetch_round5
    for sid in ("DRALACBS", "DRCLACBS"):
        rows = _rows(os.path.join(MOREFRED, sid + ".csv"))
        structure = fetch_round5.structure_events_quarterly(rows)
        assert structure == set(), (sid, sorted(structure))
        out = fetch_round5.break_census(rows, structure_events=structure, step_pct=0.30)
        assert out["refuse"] is False
        assert not any(b["coincides"] for b in out["breaks"]), (sid, out)


# ---------------------------------------------------------------- manifest
def test_manifest_rows_appended_and_pass_file_invariant():
    path = os.path.join(MOREFRED, "manifest.csv")
    rows = _read_csv(path)
    by_id = {}
    for r in rows:
        by_id.setdefault(r["series_id"], []).append(r)
    for sid in ("DRALACBS", "DRCLACBS", "WPU05320104"):
        # level row (existing convention: file=<sid>.csv, lint_pass=True)
        assert by_id.get(sid), sid
        r = by_id[sid][-1]
        assert r["lint_pass"] == "True" and r["status"] == "ok", (sid, r)
        assert r["file"] == sid + ".csv", (sid, r)
        assert os.path.exists(os.path.join(MOREFRED, r["file"])), (sid, r["file"])
        # vintage row (ICSA/PAYEMS convention: ALFRED:<sid>, lag_days=floor)
        v = by_id.get("ALFRED:" + sid, [])
        assert v, sid
        vr = v[-1]
        assert vr["lint_pass"] == "True" and vr["lag_days"], (sid, vr)
        assert os.path.exists(os.path.join(ROOT, vr["file"])), (sid, vr["file"])


def test_manifest_no_duplicate_series_rows_created():
    path = os.path.join(MOREFRED, "manifest.csv")
    rows = _read_csv(path)
    from collections import Counter
    c = Counter(r["series_id"] for r in rows)
    for sid in ("DRALACBS", "DRCLACBS", "WPU05320104", "ALFRED:DRALACBS",
                "ALFRED:DRCLACBS", "ALFRED:WPU05320104"):
        assert c[sid] == 1, (sid, c[sid])


# ---------------------------------------------------------------- DEAD_IDEAS
def test_dead_ideas_data_acquired_rows_present():
    rows = _read_csv(os.path.join(ROOT, "campaign/results/DEAD_IDEAS.csv"))
    src = [r for r in rows if "DATA_FREDMORE-R5" in r.get("source", "")]
    ideas = " || ".join(r["idea"] for r in src)
    assert "DRALACBS" in ideas and "delinquency" in ideas.lower(), ideas
    assert "WPU05320104" in ideas or "propane" in ideas.lower(), ideas
    assert all(r["status"] == "data-acquired" for r in src), [(r["status"]) for r in src]
