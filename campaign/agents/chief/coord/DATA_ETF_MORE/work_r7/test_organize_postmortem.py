"""DATA_ETF_MORE R7 charter (a): DATA_ORGANIZE post-mortem fixes, TDD RED-first.

Post-mortem source: coord/CAMP_BORROW/FINDINGS.md "LIVE INCIDENT" (2026-09-08 14:1x)
- organize_lib.write_manifest('alfred') truncated alfred/manifest.csv to 0 bytes
  mid-crash (file opened/truncated BEFORE rows[0] IndexError) -> (i) atomic write.
- The same session's sweep regenerated more_fred/manifest.csv and DESTROYED 6
  ALFRED vintage rows + lag_days fields the flat 7-col schema cannot express
  -> (ii) fail-closed regeneration guard.
- alfred/<SID>/vintage.py PIT dirs are illegal-by-construction under the layout
  test -> (iii) reserved '_pit' class (tested in campaign/team/tests/test_data_layout.py,
  per charter "Tests in YOUR dir + the layout test file").

These tests are hermetic: they monkeypatch organize_lib.DATA to a tmp dir and
never write the real data tree.
"""
import csv
import importlib.util
import os
import sys

import pytest

REPO = "/Users/daxu/software/world-trader"
LIB = f"{REPO}/campaign/team/agents/DATA_ORGANIZE/organize_lib.py"
TD = f"{REPO}/tools/quant/data/twelvedata"

_spec = importlib.util.spec_from_file_location("organize_lib", LIB)
organize_lib = importlib.util.module_from_spec(_spec)
sys.modules["organize_lib"] = organize_lib
_spec.loader.exec_module(organize_lib)

CANON = ["family", "file", "date_col", "kind", "rows", "cols", "exception"]


@pytest.fixture
def fam(tmp_path, monkeypatch):
    """A tmp data root with one family holding one curated CSV."""
    d = tmp_path / "famA"
    d.mkdir()
    with open(d / "X1.csv", "w") as fh:
        fh.write("date,close\n2026-01-02,1.0\n2026-01-03,1.1\n")
    monkeypatch.setattr(organize_lib, "DATA", str(tmp_path))
    return d


def _read_bytes(p):
    with open(p, "rb") as fh:
        return fh.read()


def _flat_row(fam_name, fname, n):
    return {"family": fam_name, "file": fname, "date_col": "date",
            "kind": "timeseries", "rows": n, "cols": "2", "exception": ""}


# ---------------------------------------------------------------- (i) atomic write

def test_t1_crash_during_row_generation_never_truncates_existing_manifest(fam):
    """The 14:10 incident: file opened/truncated, THEN rows[0] raised. The live
    manifest must be untouched if anything raises before/during the write."""
    p = fam / "manifest.csv"
    with open(p, "w", newline="") as fh:
        csv.DictWriter(fh, fieldnames=CANON).writerows([_flat_row("famA", "OLD.csv", 7)])
    before = _read_bytes(p)

    def boom(*a, **k):
        raise RuntimeError("simulated mid-run crash (the 14:10 IndexError class)")

    import organize_lib as L
    saved = L.manifest_rows
    L.manifest_rows = boom
    try:
        with pytest.raises(RuntimeError):
            L.write_manifest("famA")
    finally:
        L.manifest_rows = saved
    assert _read_bytes(p) == before, "existing manifest was modified by a crashed run"
    assert not os.path.exists(str(p) + ".tmp"), "crashed run left .tmp litter"


def test_t2_crash_midwrite_leaves_target_intact(fam):
    """Crash DURING csv serialization (partial tmp write): os.replace never runs,
    so the target keeps its pre-crash bytes and the tmp litter is cleaned."""
    p = fam / "manifest.csv"
    with open(p, "w", newline="") as fh:
        csv.DictWriter(fh, fieldnames=CANON).writerows([_flat_row("famA", "OLD.csv", 7)])
    before = _read_bytes(p)
    good = _flat_row("famA", "X1.csv", 2)
    bad = dict(good, BOGUS_EXTRA_FIELD="1")  # DictWriter raises on extra fields
    with pytest.raises(ValueError):
        organize_lib._atomic_write_manifest(str(p), [good, bad, good])
    assert _read_bytes(p) == before, "target truncated by a mid-write crash"
    assert not os.path.exists(str(p) + ".tmp")


def test_t3_successful_write_is_atomic_path_and_byte_compatible(fam):
    """The happy path writes through tmp + os.replace and produces the same bytes
    the old direct writer produced (csv default dialect, header + rows)."""
    p = organize_lib.write_manifest("famA")[0]
    got = _read_bytes(p)
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CANON)
    w.writeheader()
    w.writerows([_flat_row("famA", "X1.csv", 2)])
    assert got == buf.getvalue().encode(), "regenerated manifest bytes changed dialect"


# ------------------------------------------------- (ii) fail-closed regen guard

def test_t4_guard_refuses_rich_schema_manifest(fam):
    """A 10-col span_class-style manifest holds facts the flat write would destroy
    (my more_etf deliverable is exactly this shape). Refuse, loudly, no write."""
    p = fam / "manifest.csv"
    rich_hdr = ["symbol", "start", "end", "rows", "max_gap_days", "zero_ret_rows",
                "jump_days", "dup_dates", "span_class", "status"]
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rich_hdr)
        w.writeheader()
        w.writerow(dict(zip(rich_hdr, ["X1", "2026-01-02", "2026-01-03", "2", "1",
                                       "0", "0", "0", "pre2007", "PASS"])))
    before = _read_bytes(p)
    with pytest.raises(organize_lib.ManifestRegenerationRefused):
        organize_lib.write_manifest("famA")
    assert _read_bytes(p) == before


def test_t5_guard_refuses_lag_floor_schema(fam):
    """Charter names lag floors explicitly: a manifest carrying lag_days cannot be
    regenerated flat (the destroyed more_fred rows were exactly this)."""
    p = fam / "manifest.csv"
    rich_hdr = ["family", "file", "date_col", "kind", "rows", "cols", "exception",
                "lag_days", "role"]
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rich_hdr)
        w.writeheader()
        w.writerow(dict(zip(rich_hdr, ["famA", "X1.csv", "date", "timeseries", "2",
                                       "2", "", "35", "vintage-pit"])))
    before = _read_bytes(p)
    with pytest.raises(organize_lib.ManifestRegenerationRefused):
        organize_lib.write_manifest("famA")
    assert _read_bytes(p) == before


def test_t6_guard_refuses_subdir_artifact_refs_even_in_flat_schema(fam):
    """PIT vintage rows reference family/sub/file.csv paths - inexpressible as a
    flat top-level listing. Refuse even under a canonical header."""
    p = fam / "manifest.csv"
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CANON)
        w.writeheader()
        w.writerow({**_flat_row("famA", "sub/vintage.csv", 61), "file": "sub/vintage.csv"})
    before = _read_bytes(p)
    with pytest.raises(organize_lib.ManifestRegenerationRefused):
        organize_lib.write_manifest("famA")
    assert _read_bytes(p) == before


def test_t7_guard_allows_flat_and_absent_and_empty(fam):
    """Flat canonical (incl. header-only) and absent manifests regenerate freely -
    the guard must not wedge legitimate sweeps."""
    p = fam / "manifest.csv"
    # absent -> allowed
    p1, n1 = organize_lib.write_manifest("famA")
    assert n1 == 1 and os.path.isfile(p1)
    # flat canonical -> allowed
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CANON)
        w.writeheader()
        w.writerows([_flat_row("famA", "OLD.csv", 9)])
    p2, n2 = organize_lib.write_manifest("famA")
    assert n2 == 1
    # 0-byte (the incident damage state) -> allowed, nothing left to destroy
    open(p, "wb").close()
    p3, n3 = organize_lib.write_manifest("famA")
    assert n3 == 1


def test_t8_real_rich_manifests_are_now_guarded():
    """End-to-end on the real tree, read-only assertion: the R6-restored
    deliverables (more_etf 10-col span_class, bench_r5 27-col) must be REFUSED by
    the guard - the next organize sweep can no longer re-clobber them."""
    for fam_name in ("more_etf", "bench_r5"):
        p = f"{organize_lib.DATA}/{fam_name}/manifest.csv"
        ref = organize_lib._regen_refusals(p)
        assert ref, f"{fam_name} not guarded - a flat regeneration would destroy it"


# -------------------------------------------------------- (b) twelvedata doc-pin

def test_t9_twelvedata_manifest_stays_canonical_and_disk_accurate():
    """Charter (b) decision pin: twelvedata/manifest.csv stays in the canonical
    7-col DATA_ORGANIZE schema and must stay disk-accurate. It has NO span_class
    predecessor (no builder of mine ever wrote it; zero consumers tree-wide) and
    converting it to the 10-col ETF schema would (1) violate the canonical layout
    contract and (2) be locked-forever by the T4-T8 guard. If a future sweep
    breaks its disk accuracy, this test fires."""
    with open(f"{TD}/manifest.csv", newline="") as fh:
        rdr = csv.DictReader(fh)
        hdr = rdr.fieldnames
        rows = list(rdr)
    assert hdr == CANON, f"twelvedata manifest left canonical schema: {hdr}"
    disk = sorted(f for f in os.listdir(TD)
                  if f.endswith(".csv") and f != "manifest.csv")
    assert sorted(r["file"] for r in rows) == disk, "manifest/disk file-set mismatch"
    by_file = {r["file"]: r for r in rows}
    # spot rows: read the actual files, compare counted rows and col count
    for f in ("SPY.csv", "AAPL.csv", "AGG.csv"):
        with open(f"{TD}/{f}", newline="") as fh:
            n = sum(1 for _ in fh) - 1
            cols = next(csv.reader(fh)) if False else None
        with open(f"{TD}/{f}", newline="") as fh:
            cols = len(next(csv.reader(fh)))
        assert int(by_file[f]["rows"]) == n, f"{f} row count drifted: manifest={by_file[f]['rows']} disk={n}"
        assert int(by_file[f]["cols"]) == cols
