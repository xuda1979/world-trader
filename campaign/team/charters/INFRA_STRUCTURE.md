# INFRA_STRUCTURE — project structure, canonical layout, short code, dead-code removal
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Keep the repo clean, well-organized, discoverable, easy to maintain and extend. Enforce the
convention that files/functions/classes stay SHORT, and that every module has a one-line purpose.

## Conventions (enforce + document in campaign/team/docs/CODING_STANDARD.md)
- Function < ~40 lines · class < ~120 lines · file < ~200 lines. Split anything larger.
- One responsibility per module; name = purpose (bt/engine.py, bt/metrics.py pattern).
- No dead code: remove unreachable/unused modules (git rm + note in FINDINGS).
- No duplicated helpers: reuse campaign/bt/ + campaign/team/lib/ instead of copy-paste heredocs.
- Every new reusable helper goes in a tiny module in campaign/team/lib/ with a test.

## Deliverable
- CODING_STANDARD.md (regenerate) + a sweep report in FINDINGS.md (largest offenders -> fixed).
- Move/vendor obvious duplicate scrap scripts out of the root into team/lib or archive.

## Rules
- Refactors preserve behavior: any behavioral change needs a FAILING test first (TDD), RED->GREEN.
- Never delete a working champion input without verifying it isn't referenced (grep blobs).

## Done marker
Last line of FINDINGS.md exactly: INFRA_STRUCTURE DONE
