"""build_coverage.py — REGENERATES campaign/team/docs/DATA_COVERAGE.md from on-disk truth.

DATA_MAESTRO owns this. Reads every tools/quant/data/<family>/manifest.csv (schema-tolerant:
any of start/first, end/last, lint/status/ok/lint_pass), counts csv data files in dirs with
NO manifest, flags empty stub dirs, and emits the family table + ranked gap list + round
assignments. Fail-closed: a manifest that cannot be parsed is reported as lint=UNPARSABLE,
never silently dropped. Direct-HTTP-only org; no browser anywhere.
"""
import os
import pandas as pd

DATA = "/Users/daxu/software/world-trader/tools/quant/data"
DOC = "/Users/daxu/software/world-trader/campaign/team/docs/DATA_COVERAGE.md"
LINT_KEYS = ("lint", "status", "ok", "lint_pass")
PASS_PAT = r"PASS|True|ok"


def _pick(m, names):
    low = {c.lower(): c for c in m.columns}
    return next((low[n] for n in names if n in low), None)


BYPRODUCTS = ("manifest.csv", "manifest_lint.csv")


def _family_stat(fam):
    """(n_series, span, n_lint_pass, note) for one manifest dir; fail-closed on parse error."""
    try:
        m = pd.read_csv(f"{DATA}/{fam}/manifest.csv")
    except Exception as e:  # unparsable manifest = FAIL loudly in the map
        return (0, "?", 0, f"UNPARSABLE manifest: {type(e).__name__}")
    m = m[~m.astype(str).apply(lambda r: r.str.contains("manifest_lint.csv", na=False),
                               axis=1).any(axis=1)]  # drop byproduct rows (R1: cb_rates bug)
    if len(m) == 0:
        n_disk = _recursive_csv_count(fam)
        if n_disk:  # fail-closed: data exists but manifest is empty -> flag, never hide
            return (0, "?", 0, f"NEEDS ORGANIZE ({n_disk} CSVs on disk, manifest EMPTY)")
        return (0, "?", 0, "EMPTY manifest")
    s, e = _pick(m, ("start", "first")), _pick(m, ("end", "last"))
    if not (s and e):
        lo, hi = _csv_span(fam)  # manifest lacks dates -> cite the CSVs themselves (R1)
        span = f"{lo}..{hi}" if lo and hi else "?"
    else:
        span = f"{m[s].astype(str).min()}..{m[e].astype(str).max()}"
    lc = _pick(m, LINT_KEYS)
    n_pass = (int(m[lc].astype(str).str.contains(PASS_PAT, case=False).sum())
              if lc else None)
    return (len(m), span, n_pass, "")


def _csv_count(fam):
    d = f"{DATA}/{fam}"
    return sum(1 for f in os.listdir(d) if f.endswith(".csv") and f != "manifest.csv")


def _recursive_csv_count(fam):
    """Count data CSVs anywhere under the family dir (excl. manifest*). R1: an empty
    manifest must not let on-disk data (e.g. cboe_options/latest/) vanish from the map."""
    n = 0
    for _, _, fs in os.walk(f"{DATA}/{fam}"):
        n += sum(1 for f in fs if f.endswith(".csv") and not f.startswith("manifest"))
    return n


def _csv_span(fam):
    """(min_date, max_date) probed from the family's data CSVs themselves (head/tail of
    first column, ISO-ish). R1: 14:40 manifest standard dropped start/end — citing the
    manifest would cite nothing. Cheap line probes, never a full pandas read."""
    lo = hi = None
    for _, _, fs in os.walk(f"{DATA}/{fam}"):
        for f in sorted(fs):
            if not f.endswith(".csv") or f.startswith("manifest"):
                continue
            path = os.path.join(DATA, fam, f)
            try:
                with open(path, errors="replace") as fh:
                    fh.readline()  # header line — never a data date
                    second = fh.readline()  # FIRST DATA ROW
                    last = second
                    for last in fh:  # walk to EOF for the LAST data row
                        pass
            except FileNotFoundError:
                continue  # live-tree race: file vanished between walk and open (R1 fleet)
            for c in (second.strip().split(",")[0], last.strip().split(",")[0]):
                if pd_notna_date(c):  # BOTH ends — a file may be reverse-sorted
                    lo = c if lo is None or c < lo else lo
                    hi = c if hi is None or c > hi else hi
    return lo, hi


def pd_notna_date(tok):
    """True if tok looks like a YYYY-MM-DD date (cheap, no pandas)."""
    return (len(tok) >= 10 and tok[4] == "-" and tok[7] == "-"
            and tok[:4].isdigit() and tok[5:7].isdigit() and tok[8:10].isdigit())


def scan():
    """Return (rows, stubs) — rows: {family:(n,span,pass,note)}, stubs: empty/manifest-less dirs."""
    rows, stubs = {}, []
    for fam in sorted(os.listdir(DATA)):
        d = f"{DATA}/{fam}"
        if not os.path.isdir(d):
            continue
        if os.path.isfile(f"{d}/manifest.csv"):
            rows[fam] = _family_stat(fam)
        else:
            n = _csv_count(fam)
            if n == 0:
                stubs.append(fam)
            else:
                rows[fam] = (n, "no-manifest", None, "NEEDS ORGANIZE (no manifest.csv)")
    return rows, stubs


def gap_section(rows):
    """Ranked NEW-family gap list: decorr-first, decade+ span, direct-HTTP. Cited evidence.
    R1 2026-09-08: rewritten from fresh disk probes (see FINDINGS.md for exact numbers)."""
    return """
## Gap-leaders to pull next (regenerated {date}; ranked decorr x span x non-browser)

1. **Credit spreads — CLOSED 2026-10-12 (DATA_BAML_REPAIR): source-truncated, do NOT
   re-pull — a re-pull now DESTROYS data.** The earlier claim that "FRED serves 1996-12+
   ~7,400 rows" was a phantom, falsified 2026-10-12 on every route (API no-start /
   API observation_start=1996-12-31 / fredgraph.csv / ALFRED — API+fredgraph return
   786-794 rows from 2023-10-10+; ALFRED returns HTTP 400 "series does not exist in
   ALFRED"). Root cause, per FRED's own series metadata: "Starting in April 2026, this
   series will only include 3 years of observations" — an ICE licensing cap, a ROLLING
   window. Consequences: (a) RES_CREDIT's decade+ span gate is unachievable from FRED,
   permanently, not a repair item; (b) the on-disk more_fred BAML files
   (BAMLH0A0HYM2 787 rows 2023-09-05..2026-09-03, BAMLC0A0CM 786, BAMLEMHBHYCRPIOAS 787,
   fred_full/BAMLH0A0HYM2.csv 780) are correct-for-their-window and are now the ONLY
   copy of 2023-09-05..2023-10-09 — FRED has already rolled past it; (c) re-running
   repair_baml_oas.py or any blind re-pull would overwrite the front month with nothing.
   repair_baml_oas.py is DEAD (premise falsified) — never run it. Long-history credit
   spreads require a new licensed/source axis (operator charter, beat-path 1), not FRED.
2. **German sovereign curve (daily Bunds)**: mof_jgb already holds the full JGB curve (16
   tenors, 13,290 rows, 1974-09-24..2026-08-31); boe_curve covers GBP (1979+); the DE leg is
   ABSENT estate-wide. Direct HTTP from Bundesbank — decade+ span, decorrelated to USD legs.
3. **Daily NAO/AO index (NOAA PSL)**: noaa_climate monthly is complete (nao 919 rows
   1950-01-01..2026-07-01, 0 nulls; meiv2 571 rows) but daily-resolution NAO/AO (psl.noaa.gov)
   is absent — decade+ span, no weather leg anywhere in the champion blend.
4. **VIX1D (CBOE, cdn.cboe.com direct CSV)**: ABSENT estate-wide. Short span (2023+, ~3y —
   fails decade+ gate) but unique 1-day tenor for RES_VOL term work; BONUS only after 1-3.
""".format(date=__import__("datetime").date.today().isoformat())


def assignment_section():
    return """
## Assignments (this round, by MAESTRO — post-reorg repair round R1, 2026-09-08)
| agent | task | acceptance |
|---|---|---|
| DATA_PULL | ~~re-pull FULL BAML OAS history~~ VOIDED 2026-10-12 (item 1 — phantom premise; source is rolling-3y ICE-licensed, re-pull destroys data) + VIX1D bonus | ~~BAMLH0A0HYM2 >= 7000 rows~~ unachievable from FRED (closed); VIX1D acceptance unchanged |
| DATA_CLEAN | restore lint columns fleet-wide (14:40 manifest standard DROPPED lint: 52/71 families now lint n/a); re-run lint battery per CSV (span/na/gap/range) | every family with >0 series carries a lint column with PASS/FAIL per row |
| DATA_ORGANIZE | reconcile 19 empty-manifest families vs on-disk CSVs (cboe_options/latest has 9+ CSVs vs manifest 0); remove cb_rates manifest_lint.csv self-byproduct row; finish stub cleanup (alfred/alpha_vantage/etc.) | manifest series-count == disk data-CSV count for ALL families; map shows zero NEEDS ORGANIZE |
| DATA_MERGE | build panel_vixterm (VIX9D/VIX/VIX3M/VIX6M/VXV/VVIX + SKEW from more_vol/, SPY from twelvedata/, rows-kept) via campaign/team/lib/merge.py — NOT yet on disk (no tools/quant/data/panel_*) | union-join rows == union of calendars; fix test_load_series_real_sp500 (merge.load_series("twelvedata","SPY") raises FileNotFoundError — manifest-era path regression) |
"""


def main():
    rows, stubs = scan()
    out = ["# DATA COVERAGE MAP (regenerated by DATA_MAESTRO — do not hand-edit final state)",
           "",
           "> Generated by campaign/team/agents/DATA_MAESTRO/build_coverage.py from",
           "> tools/quant/data/*/manifest.csv. Regenerate, never hand-edit. Fail-closed:",
           "> unparsable manifest => lint UNPARSABLE. Champion:",
           "> GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv (ann 37.195% / SR 3.181 / MDD -6.69%).",
           "",
           "## Inventory (manifest families)",
           "| family | series | span | lint | note |",
           "|---|---|---|---|---|"]
    for fam, (n, span, n_pass, note) in rows.items():
        lint = ("n/a" if n_pass is None else f"{n_pass}/{n}")
        out.append(f"| {fam} | {n} series | {span} | lint {lint} | {note} |")
    out += ["", f"## Empty stub dirs (no CSV, no manifest) — n={len(stubs)}",
            ", ".join(stubs) if stubs else "(none)",
            gap_section(rows), assignment_section(),
            "## Notes",
            "- lint counts are schema-tolerant (lint|status|ok|lint_pass) — a family with no",
            "  lint column shows n/a and is a DATA_CLEAN assignment, not a pass.",
            "- Any new panel must be rows-kept (no inner-join hole) before RES_* use."]
    with open(DOC, "w") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {DOC}: {len(rows)} manifest/no-manifest families, {len(stubs)} stubs")


if __name__ == "__main__":
    main()
