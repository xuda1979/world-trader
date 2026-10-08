#!/usr/bin/env python3
"""RAW-DATA PROVENANCE MANIFEST — closes open item (b) of the b79d7b87 memo.

`tools/quant/data/` is wholly gitignored (root .gitignore line 5): every raw
vintage there is single-copy. The diescrack raw loss (recovered 2026-10-08) and
the H1 20260930 near-loss are this class. This tool does NOT move raw bytes
into git; it pins the tree CONTENTS so silent mutation/loss is detectable and
the 2026-10-08 recovery state is the auditable baseline.

Usage:
  python3 campaign/scripts/raw_data_manifest.py --emit     # write manifest
  python3 campaign/scripts/raw_data_manifest.py --verify   # fail-closed diff (exit 1 on ANY delta)

Determinism: rows sorted by relpath; sha16 = sha256(file bytes)[:16]; no
mtimes, no uid, no absolute paths -> byte-stable across checkouts of the same
data state and across macOS/Linux.

Rules:
  * --emit is SAFE: it only writes campaign/results/RAW_DATA_MANIFEST.csv.
  * --verify is FAIL-CLOSED: extra file, missing file, size change, or content
    change each exit 1 and NAME the offending relpath(s).
  * Known-volatile files (live-updating caches) are EXCLUDED and pinned by
    pattern in EXCLUDE so the manifest stays stable day-to-day; every exclusion
    is a deliberate, documented choice.
"""
import argparse
import csv
import hashlib
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_TREE = os.path.join(ROOT, "tools", "quant", "data")
MANIFEST = os.path.join(ROOT, "campaign", "results", "RAW_DATA_MANIFEST.csv")

# Files that update on a live schedule (touched by downloads in ordinary ops)
# are excluded from content-pinning: a manifest that flips every fetch would be
# pinned, re-pinned, and eventually ignored. Loss of these is recoverable by
# re-download, which is exactly what the per-axis README/manifest documents.
EXCLUDE_DIRS = {"__pycache__"}
EXCLUDE_SUFFIXES = (".pyc",)


def sha16_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def walk():
    """Yield (relpath, bytes, sha16) for every pinned file, sorted by relpath."""
    rows = []
    for dirpath, dirnames, filenames in os.walk(DATA_TREE):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS)
        for fn in sorted(filenames):
            if fn.endswith(EXCLUDE_SUFFIXES):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, DATA_TREE)
            rows.append((rel, os.path.getsize(full), sha16_file(full)))
    rows.sort(key=lambda r: r[0])
    return rows


def write_manifest(rows):
    with open(MANIFEST, "w", newline="") as f:
        f.write("# RAW-DATA PROVENANCE MANIFEST (machine-generated) -- "
                "regen: python3 campaign/scripts/raw_data_manifest.py --emit\n")
        w = csv.writer(f)
        w.writerow(["relpath", "bytes", "sha16"])
        w.writerows(rows)


def read_manifest():
    with open(MANIFEST) as f:
        rows = [r for r in csv.reader(f) if r and not r[0].startswith("#")]
    return {(r[0], int(r[1]), r[2]) for r in rows[1:]}


def verify():
    disk = set(walk())
    pinned = read_manifest()
    extra = sorted(disk - pinned)
    missing = sorted(pinned - disk)
    if extra:
        print("EXTRA on disk (not in manifest):")
        for r in extra:
            print(f"  + {r[0]} ({r[1]} bytes, sha16 {r[2]})")
    if missing:
        print("MISSING on disk (pinned but lost -- LOSS-CLASS ALARM):")
        for r in missing:
            print(f"  - {r[0]} ({r[1]} bytes, sha16 {r[2]})")
    if extra or missing:
        print(f"VERIFY RED: {len(extra)} extra, {len(missing)} missing. "
              "If the change is deliberate: re-run --emit, re-pin the "
              "baseline in test_raw_data_manifest.py, and commit BOTH with a "
              "ledger note. If not deliberate: investigate before touching "
              "anything else.")
        return 1
    print(f"VERIFY GREEN: {len(disk)} files pinned, byte-identical.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--emit", action="store_true",
                   help="write the manifest from the current tree (safe)")
    g.add_argument("--verify", action="store_true",
                   help="fail-closed diff of tree vs committed manifest")
    a = ap.parse_args()
    if not os.path.isdir(DATA_TREE):
        sys.exit(f"FATAL: data tree missing: {DATA_TREE}")
    if a.emit:
        rows = walk()
        write_manifest(rows)
        axes = {r[0].split("/")[0] for r in rows}
        h = hashlib.sha256()
        for r in rows:
            h.update(r[2].encode())
        print(f"EMIT: {len(rows)} files across {len(axes)} axes -> {MANIFEST}")
        print(f"tree content sha16: {h.hexdigest()[:16]}")
        return 0
    return verify()


if __name__ == "__main__":
    sys.exit(main())
