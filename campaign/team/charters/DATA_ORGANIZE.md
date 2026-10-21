# DATA_ORGANIZE — canonical data layout & naming
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Make every dataset discoverable and consistently structured. Enforce the canonical convention:
one dataset = one dir = one README + manifest.csv describing columns/spans.

## Scope
- tools/quant/data/<family>/ must contain: <SYMB>.csv (columns date,<fields>), manifest.csv,
  README.md (source URL, update cadence, license).
- Uniform date column 'date' (YYYY-MM-DD / YYYYMMDD normalized to ISO), sorted ascending.
- No nested junk, no stray .py inside data dirs; point to parsers/ in campaign/tools instead.

## Deliverable
- A canonicalization report in FINDINGS.md (every dir audited, what moved/renamed, before->after).
- Fix NO data values (that's DATA_CLEAN's job) — only layout/names/duplicates of files.

## Rules
- Do not delete any CSV. Move/rename with `git mv` where tracked; note untracked moves in report.
- Keep a backup note (dirs are git-ignored blobs; record a manifest hash first).

## Done marker
Last line of FINDINGS.md exactly: DATA_ORGANIZE DONE
