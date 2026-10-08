"""RAW-DATA PROVENANCE MANIFEST pins (2026-10-08, session post-ITER60).

Closes open item (b) of the b79d7b87 decision memo: `tools/quant/data/` is
wholly gitignored (see root .gitignore line 5), so every raw vintage there is
single-copy. The diescrack raw loss (recovered 2026-10-08) and the H1 20260930
near-loss are both this loss-class. This manifest does NOT move the raw bytes
into git (repo bloat + binary churn); it pins the tree CONTENTS so that any
silent mutation, truncation, or loss is detectable and the 2026-10-08 recovery
state is the auditable baseline.

Design (mirrors the champion-card pattern: script generates, test pins):
  * campaign/scripts/raw_data_manifest.py --emit   writes
    campaign/results/RAW_DATA_MANIFEST.csv (one row per file: relpath, bytes,
    sha256[16], mtime-free) + a one-line header comment for regen.
  * --verify re-walks the tree and diffs against the committed manifest
    FAIL-CLOSED: any extra/missing/changed file is reported and exits 1.
  * Determinism: files sorted by relpath; sha256 of file BYTES only (no mtime,
    no uid, no platform paths) so the manifest is byte-stable across checkouts
    of the same data state and across macOS/Linux.

TDD order: this file landed RED (no script, no manifest), then the script +
manifest landed GREEN.
"""
import subprocess
import sys
import csv
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SCRIPT = os.path.join(ROOT, "campaign", "scripts", "raw_data_manifest.py")
MANIFEST = os.path.join(ROOT, "campaign", "results", "RAW_DATA_MANIFEST.csv")
DATA_TREE = os.path.join(ROOT, "tools", "quant", "data")

# ---------------------------------------------------------------- reality pins
def test_manifest_exists_and_is_csv():
    assert os.path.exists(MANIFEST), (
        "campaign/results/RAW_DATA_MANIFEST.csv missing -- run "
        "`python3 campaign/scripts/raw_data_manifest.py --emit`")
    with open(MANIFEST) as f:
        rows = list(csv.reader(f))
    assert rows, "manifest empty"
    # header comment line is required for regen instructions
    first = rows[0][0] if rows[0] else ""
    assert first.startswith("#"), "manifest must start with a # regen comment line"
    hdr = rows[1]
    assert hdr[:3] == ["relpath", "bytes", "sha16"], f"bad header: {hdr[:3]}"


def test_manifest_covers_every_axis_dir_on_disk():
    """Every top-level axis dir under tools/quant/data/ must appear in the
    manifest. A NEW axis dir acquired later turns this RED until --emit is
    re-run -- deliberate: acquisitions must re-snapshot the tree."""
    with open(MANIFEST) as f:
        rows = [r for r in csv.reader(f) if r and not r[0].startswith("#")]
    covered = {r[0].split("/")[0] for r in rows[1:]}
    on_disk = {d for d in os.listdir(DATA_TREE)
               if os.path.isdir(os.path.join(DATA_TREE, d))}
    missing = on_disk - covered
    assert not missing, (
        f"axis dir(s) on disk but NOT in manifest: {sorted(missing)} -- "
        "run --emit to re-snapshot, then commit with explicit pathspec")


def test_manifest_rows_are_sorted_unique_and_hashed():
    with open(MANIFEST) as f:
        rows = [r for r in csv.reader(f) if r and not r[0].startswith("#")]
    relpaths = [r[0] for r in rows[1:]]
    assert relpaths == sorted(relpaths), "manifest not sorted by relpath"
    assert len(relpaths) == len(set(relpaths)), "duplicate relpath rows"
    for r in rows[1:]:
        assert len(r) == 3, f"row must be relpath,bytes,sha16: {r}"
        assert len(r[2]) == 16, f"sha16 must be 16 hex chars: {r}"
        int(r[1])  # bytes must parse as int


def test_verify_mode_is_green_and_fail_closed():
    """--verify must exit 0 on the committed state (idempotent re-walk)."""
    p = subprocess.run([sys.executable, SCRIPT, "--verify"],
                       capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, (
        f"--verify RED on the committed data state:\n{p.stdout}\n{p.stderr}")


def test_verify_detects_tamper_fail_closed():
    """--verify must exit NONZERO when a file inside the tree changes.
    Tamper with a throwaway copy-safe file: append to an existing CSV's mtime
    is destructive, so instead we ADD a new file and require detection, then
    remove it (the add-path is the diescrack-recovery-loss inverse: a file
    going MISSING must equally fail). Both paths share the same diff code."""
    canary = os.path.join(DATA_TREE, "zz_manifest_tamper_canary.tmp")
    try:
        with open(canary, "w") as f:
            f.write("tamper\n")
        p = subprocess.run([sys.executable, SCRIPT, "--verify"],
                           capture_output=True, text=True, cwd=ROOT)
        assert p.returncode != 0, "--verify GREEN despite an extra file -- fail-open bug"
        assert "zz_manifest_tamper_canary.tmp" in p.stdout + p.stderr, (
            "verify must NAME the offending file")
    finally:
        if os.path.exists(canary):
            os.remove(canary)
    # and the tree must verify clean again after removal
    p = subprocess.run([sys.executable, SCRIPT, "--verify"],
                       capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, "verify not green after canary removal"


def test_pinned_baseline_snapshot():
    """Pin the 2026-10-08 recovery-state baseline: axis count + total files +
    the tree sha16 (sha256 over the manifest's sha16 column in order). Any
    change to the data tree -- acquisition, refresh, loss -- moves this and
    must be re-pinned DELIBERATELY with a ledger note."""
    with open(MANIFEST) as f:
        rows = [r for r in csv.reader(f) if r and not r[0].startswith("#")]
    files = rows[1:]
    axes = {r[0].split("/")[0] for r in files}
    assert len(axes) == 86, (
        f"axis count moved from 86: {len(axes)} -- if a new axis was acquired, "
        "update this pin AND the ledger note in the same commit")
    assert len(files) == 11694, (
        f"file count moved from 11694: {len(files)} -- re-run --emit and "
        "re-pin if the change is deliberate")
    import hashlib
    h = hashlib.sha256()
    for r in files:
        h.update(r[2].encode())
    tree_sha16 = h.hexdigest()[:16]
    assert tree_sha16 == "519df8283c781911", (
        f"data-tree content hash moved from 519df8283c781911: {tree_sha16}")
