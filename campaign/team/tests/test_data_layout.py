"""DATA_ORGANIZE layout contract for tools/quant/data/ (TDD, RED first).

Pins the canonical convention (charter campaign/team/charters/DATA_ORGANIZE.md):
  one dataset = one dir = README.md + manifest.csv; uniform 'date' first column
  (exceptions must be pinned in date_col_exceptions.json, two-way fail-closed);
  no junk files, no code, no caches, no spreadsheets inside the data tree.
Layout only — data VALUES are DATA_CLEAN's job and are never touched here.
"""
import csv
import json
import os

DATA = "/Users/daxu/software/world-trader/tools/quant/data"
AG = "/Users/daxu/software/world-trader/campaign/team/agents/DATA_ORGANIZE"
EXC = f"{AG}/date_col_exceptions.json"
DEBT = f"{AG}/legacy_fetchers_debt.json"
RAW = f"{AG}/raw_subdir_convention.json"
JUNK = {"__pycache__", ".pytest_cache", ".DS_Store"}


def _load(path):
    with open(path) as fh:
        return json.load(fh)


def _is_debt(path):
    import fnmatch
    rel = os.path.relpath(path, DATA)
    return any(fnmatch.fnmatch(rel, p) for p in _load(DEBT)["pinned"])


def _in_reserved_raw(path):
    rel = os.path.relpath(path, DATA).split(os.sep)
    if len(rel) > 2 and rel[1] in set(_load(RAW)["reserved"]):
        return True
    return len(rel) > 2 and rel[1] in _pit_dirs(rel[0])  # _pit class (R7)


def _pit_dirs(fam):
    """'_pit' raw-subdir class: a family subdir holding a PIT vintage.csv
    (release-event schema, vendor-owned format — DATA_PULL/DATA_CLEAN domain).
    R7 reservation: these dirs were illegal-by-construction before, which is the
    mechanism that re-flagged alfred/<SID>/ after the 14:1x destruction
    (CAMP_BORROW FINDINGS LIVE INCIDENT escalation #2)."""
    root = os.path.join(DATA, fam)
    out = []
    try:
        subs = os.listdir(root)
    except OSError:
        return out
    for sub in subs:
        p = os.path.join(root, sub)
        if (os.path.isdir(p) and not os.path.islink(p)
                and os.path.isfile(os.path.join(p, "vintage.csv"))):
            out.append(sub)
    return out


def _fams():
    return sorted(d for d in os.listdir(DATA)
                  if os.path.isdir(os.path.join(DATA, d))
                  and not d.startswith("."))


def _walk():
    for root, dirs, files in os.walk(DATA):
        dirs[:] = [d for d in dirs if d != ".git"]  # never prune JUNK pre-hoc:
        for f in files:                              # pruned dirs are invisible
            yield os.path.join(root, f)              # to junk checks (fail-open)


def _first_col(path):
    with open(path, errors="replace") as fh:
        line = fh.readline()
    return line.split(",")[0].strip().strip('"').lower()


def test_root_has_only_dirs():
    strays = [f for f in os.listdir(DATA)
              if os.path.isfile(os.path.join(DATA, f))]
    assert strays == [], f"stray files at data root: {strays}"


def test_no_cache_or_junk_anywhere():
    hits = [p for p in _walk() if os.path.basename(p) in JUNK
            or any(j in p.split(os.sep) for j in JUNK)]
    assert hits == [], f"cache/junk in data tree: {hits[:10]}"


def test_no_code_or_spreadsheets_in_data_tree():
    bad = [p for p in _walk()
           if p.endswith((".py", ".pyc", ".xlsx", ".xls")) and not _is_debt(p)]
    assert bad == [], f"code/spreadsheet files in data tree: {bad[:10]}"


def test_parser_debt_pin_is_two_way():
    pins = [p for p in _load(DEBT)["pinned"]]
    import fnmatch
    actual = [os.path.relpath(p, DATA) for p in _walk() if p.endswith(".py")]
    stale = [p for p in pins
             if "*" not in p and not os.path.isfile(os.path.join(DATA, p))]
    unknown = sorted(set(actual) - set(pins)
                     - {a for p in pins if "*" in p
                        for a in actual if fnmatch.fnmatch(a, p)})
    assert not stale, f"debt pins no longer on disk (migrate or delete): {stale}"
    assert not unknown, f"unpinned .py in data tree (pin or migrate): {unknown}"


def test_no_empty_family_dirs():
    empty = [d for d in _fams() if not os.listdir(os.path.join(DATA, d))]
    assert empty == [], f"empty family dirs: {empty}"


def test_every_family_has_readme_and_manifest():
    missing = [(d, f) for d in _fams() for f in ("README.md", "manifest.csv")
               if not os.path.isfile(os.path.join(DATA, d, f))]
    assert missing == [], f"missing canonical files: {missing}"


def test_raw_subdirs_use_reserved_names():
    rogue = []
    reserved = set(_load(RAW)["reserved"])
    for d in _fams():
        pits = _pit_dirs(d)
        for sub in os.listdir(os.path.join(DATA, d)):
            p = os.path.join(DATA, d, sub)
            if os.path.isdir(p) and not os.path.islink(p):
                if d.startswith(".") or sub in reserved or sub in pits:
                    continue
                # a nested dir is a raw drop ONLY if it holds vendor files
                if any(f.endswith((".csv", ".zip")) for f in os.listdir(p)):
                    rogue.append(f"{d}/{sub}")
    assert rogue == [], f"unpinned raw subdirs: {rogue}"


def test_pit_class_is_content_classified_two_way():
    """R7: the _pit class is granted BY CONTENT (a release-event vintage.csv
    inside), so it cannot be squatted (a stray subdir, or one holding an
    arbitrary file named vintage.csv, stays rogue / is re-flagged) and can
    never go stale (a _pit dir that loses its vintage.csv de-classifies).
    Two-way fail-closed survives by construction."""
    for fam in _fams():
        for sub in _pit_dirs(fam):
            p = os.path.join(DATA, fam, sub)
            assert os.path.isfile(os.path.join(p, "vintage.csv")), \
                f"_pit classification without vintage.csv: {fam}/{sub}"
            inner = os.listdir(p)
            assert inner == ["vintage.csv"], \
                f"_pit dir holds non-vintage files: {fam}/{sub} -> {inner}"
            with open(os.path.join(p, "vintage.csv"), errors="replace") as fh:
                hdr = fh.readline().strip().split(",")
            assert hdr[:2] == ["release_date", "observation_date"], \
                f"_pit vintage.csv not release-event schema: {fam}/{sub} hdr={hdr}"


def test_pit_vintage_files_exempt_from_date_column_rule():
    """vintage.csv is release-event schema (release_date,observation_date,value):
    first col is NOT 'date' by design. As reserved-raw-class content it is
    exempt from the uniform-date rule (and from DATA_ORGANIZE's flat manifest
    listing, handled by organize_lib's regen guard, not here)."""
    for fam in _fams():
        for sub in _pit_dirs(fam):
            p = os.path.join(DATA, fam, sub, "vintage.csv")
            assert _in_reserved_raw(p), f"{fam}/{sub}/vintage.csv not class-exempt"


def test_manifests_canonical_schema_and_complete():
    """manifest.csv contract: canonical header; one row per non-manifest CSV;
    no self-listing; empty family => header-only manifest (not corrupt).
    R7 exception: families pinned in rich_manifest_registry.json hold a
    purpose-built schema that carries facts the flat schema cannot express
    (span_class, PIT vintage rows, corr pins). Those must keep ALL registered
    columns (two-way: losing one fails) and keep the flat file-set contract."""
    import glob
    registry = _load(f"{AG}/rich_manifest_registry.json")["pinned"]
    bad = []
    for mf in sorted(glob.glob(f"{DATA}/*/manifest.csv")):
        fam = os.path.basename(os.path.dirname(mf))
        try:
            with open(mf, errors="replace") as fh:
                rdr = csv.DictReader(fh)
                hdr = rdr.fieldnames
                rows = list(rdr)
            if fam in registry:
                reg = registry[fam]
                missing = [c for c in reg["required_cols"] if c not in (hdr or [])]
                if missing:
                    bad.append((fam, f"RICH_PIN_LOST_COLS:{missing}")); continue
                if hdr == ["family", "file", "date_col", "kind",
                           "rows", "cols", "exception"]:
                    bad.append((fam, "RICH_PIN_FLATTENED(registry entry stale)")); continue
                if reg.get("disk_check") == "top_level_csv":
                    key = reg["row_key"]
                    disk = sorted(f[:-4] for f in os.listdir(os.path.join(DATA, fam))
                                  if f.endswith(".csv") and f != "manifest.csv")
                    got = sorted(r[key] for r in rows)
                    if got != disk:
                        bad.append((fam, f"STALE:disk={len(disk)} manifest={len(got)}"))
                continue  # other rich pins: content owned by their own suites
            elif hdr != ["family", "file", "date_col", "kind",
                         "rows", "cols", "exception"]:
                bad.append((fam, f"BAD_SCHEMA:{hdr}")); continue
            if any(r["file"] == "manifest.csv" for r in rows):
                bad.append((fam, "SELF_LISTED")); continue
            disk = sorted(os.path.basename(p) for p in glob.glob(f"{DATA}/{fam}/*.csv")
                          if os.path.basename(p) != "manifest.csv")
            got = sorted(os.path.basename(r["file"]) for r in rows)
            if got != disk:
                bad.append((fam, f"STALE:disk={len(disk)} manifest={len(got)}"))
        except Exception as e:
            bad.append((fam, f"UNREADABLE:{e}"))
    assert bad == [], f"manifest contract violations: {bad[:10]}"


def test_every_family_dir_gets_a_manifest():
    import glob
    fams = [d for d in os.listdir(DATA)
            if os.path.isdir(os.path.join(DATA, d)) and not d.startswith(".")]
    missing = [d for d in fams
               if not os.path.isfile(os.path.join(DATA, d, "manifest.csv"))]
    assert missing == [], f"families without manifest.csv: {missing}"


def test_csvs_uniform_date_column_with_pinned_exceptions():
    assert os.path.isfile(EXC), f"exceptions pin missing: {EXC}"
    exc = set(_load(EXC))
    off = []
    for p in _walk():
        rel = os.path.relpath(p, DATA)
        if not p.endswith(".csv") or "manifest" in os.path.basename(rel):
            continue
        if _in_reserved_raw(p):
            continue  # vendor-verbatim raw drops are DATA_CLEAN's domain
        if _first_col(p) != "date":
            off.append(rel)
    unknown = sorted(set(off) - exc)
    stale = sorted(exc - set(off))
    assert not unknown, f"non-date CSVs not pinned in exceptions: {unknown[:10]}"
    assert not stale, f"exceptions no longer valid (fix or delete): {stale[:10]}"
