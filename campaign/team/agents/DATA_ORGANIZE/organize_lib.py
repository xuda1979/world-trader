"""organize_lib.py — DATA_ORGANIZE helpers (layout-only, stdlib).

Generates README.md / manifest.csv per family dir. Never edits CSV values.

R7 post-mortem hardening (DATA_ETF_MORE, 2026-09-08, TDD RED-first; post-mortem
source: coord/CAMP_BORROW/FINDINGS.md "LIVE INCIDENT" 14:1x):
  (i)  write_manifest is ATOMIC (tmp + os.replace): a crash mid-generation can
       never leave a truncated/0-byte manifest (the alfred 14:10 damage).
  (ii) fail-closed regeneration guard: refuses to regenerate a manifest that
       currently references artifacts the flat 7-col schema cannot express
       (span_class/lag_days-style rich columns, PIT vintage rows) — the
       destroyed more_fred lag-floor + ALFRED vintage rows class.
  (iii) the _pit raw-subdir class lives in raw_subdir_convention.json +
       campaign/team/tests/test_data_layout.py (not here).
"""
import csv, glob, json, os, datetime

DATA = "/Users/daxu/software/world-trader/tools/quant/data"
AG = os.path.dirname(os.path.abspath(__file__))

CANON_FIELDS = ["family", "file", "date_col", "kind", "rows", "cols", "exception"]


class ManifestRegenerationRefused(RuntimeError):
    """write_manifest refuses: regeneration would destroy inexpressible facts."""


def _regen_refusals(path):
    """Reasons regeneration is refused for the manifest at `path` (empty = ok).

    Fail-closed on anything unprovable; absent/0-byte manifests are the incident
    damage state — nothing left to destroy, so regeneration is allowed there.
    """
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return []
    try:
        with open(path, errors="replace", newline="") as fh:
            rdr = csv.DictReader(fh)
            hdr, rows = rdr.fieldnames, list(rdr)
    except Exception as e:
        return [f"UNREADABLE({e!r:.60})"]
    if hdr != CANON_FIELDS:
        return [f"RICH_SCHEMA(hdr={hdr})"]  # facts flat write would destroy
    for r in rows:
        f = r.get("file") or ""
        if "/" in f or "\\" in f:
            return [f"SUBDIR_ARTIFACT_REF({f})"]  # PIT vintage-row class
        if None in r:  # ragged row: more values than the header names
            return [f"RAGGED_ROW({f})"]
    return []


def _atomic_write_manifest(path, rows, fields=CANON_FIELDS):
    """Write rows to `path` via tmp file + os.replace (atomic on same fs)."""
    tmp = f"{path}.tmp"
    try:
        with open(tmp, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()  # header-only manifest = family with 0 data CSVs
            w.writerows(rows)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def first_col(path):
    with open(path, errors="replace") as fh:
        return fh.readline().split(",")[0].strip().strip('"').lower()


def csv_stats(path):
    with open(path, errors="replace") as fh:
        rows = list(csv.reader(fh))
    hdr = rows[0]
    n = len(rows) - 1
    return hdr, n


def manifest_rows(fam, exc):
    out = []
    csvs = [f for f in sorted(glob.glob(f"{DATA}/{fam}/*.csv"))
            if os.path.basename(f) != "manifest.csv"]  # never list self
    for f in csvs:
        b = os.path.basename(f)
        rel = f"{fam}/{b}"
        try:
            hdr, n = csv_stats(f)
            datecol = (first_col(f) == "date")
        except Exception:
            hdr, n, datecol = ["ERR"], 0, False
        kind = "timeseries" if datecol else ("snapshot" if "snapshot" in b
                                             else "non-date(see exceptions)")
        out.append({"family": fam, "file": b, "date_col": "date" if datecol else "NO",
                    "kind": kind, "rows": n, "cols": len(hdr),
                    "exception": "Y" if rel in exc else ""})
    return out


def exceptions():
    with open(f"{AG}/date_col_exceptions.json") as fh:
        return set(json.load(fh))


def write_readme(fam, src, cadence, license_):
    p = f"{DATA}/{fam}/README.md"
    with open(p, "w") as fh:
        fh.write(f"# {fam}\n\n- Source: {src}\n- Update cadence: {cadence}\n"
                 f"- License: {license_}\n- Layout: canonical "
                 f"(campaign/team/charters/DATA_ORGANIZE.md)\n"
                 f"- Generated: {datetime.date.today().isoformat()}\n")
    return p


def write_manifest(fam):
    rows = manifest_rows(fam, exceptions())
    p = f"{DATA}/{fam}/manifest.csv"
    refusal = _regen_refusals(p)
    if refusal:
        raise ManifestRegenerationRefused(
            f"refusing to regenerate {p}: {refusal[0]} — the flat schema cannot "
            f"express the artifacts it currently references; migrate the family "
            f"to a purpose-built manifest instead")
    _atomic_write_manifest(p, rows)
    return p, len(rows)
