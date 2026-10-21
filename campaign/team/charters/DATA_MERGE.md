# DATA_MERGE — join families into canonical panels (rows-kept, no inner-join holes)
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Build the merge layer between raw families and engine inputs. A RES_* agent must be able to
load ONE clean panel, not stitch 5 CSVs by hand.

## Contract
- Merges use ROWS-KEPT (union/outer) calendar semantics: never inner-join that silently drops
  NYSE-closed rows (the L16 hole). Backfill forward where economics allow; disclose.
- Dates normalized to ISO; aligned on the canonical business calendar (campaign/bt/align.py).
- Output: tools/quant/data/panel_<name>/<name>.csv + manifest (columns, span, row count, source map)
  and a `campaign/team/agents/DATA_MERGE/` repro script (short) + FINDINGS.md rows.
- Add a small smoke test that the joined panel has NO phantom drop (row count == union of calendars).

## Rules
- TDD for any join/align helper. Root-cause (systematic-debugging) any row-count surprise.

## Done marker
Last line of FINDINGS.md exactly: DATA_MERGE DONE
