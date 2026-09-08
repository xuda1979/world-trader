# CODING_STANDARD — short, clean, maintainable code (enforced by INFRA_STRUCTURE)

## Limits (hard)
- Function: <= 40 lines body · Class: <= 120 lines · File module: <= 200 lines.
- One responsibility per module; module name = its purpose (bt/engine.py pattern).
- Docstring: one line stating what the module/function does; add args/returns only when non-obvious.

## Structure
- Reuse campaign/bt/ + campaign/team/lib/ instead of copy-pasting heredocs.
- New reusable helper -> a tiny module in campaign/team/lib/ with a unit test.
- No dead code: remove unreachable modules (git rm + FINDINGS note). No duplicate helpers.

## Behavior preservation
- Refactors must not change numbers: any behavior change needs a FAILING test first (TDD, RED->GREEN).
- Grep champion-input blobs before deleting anything (verify_champion_r3_cmd.sh sleeve map).

## Data
- Canonical dir per dataset (tools/quant/data/<family>/), manifest.csv + README.md.
- Date column 'date' ISO; sorted ascending; rows-kept merges (no inner-join holes).
- Free data = DIRECT HTTP only. NEVER automate/control/touch the user's browser (permanent directive).

## Honesty (ai-devops + superpowers)
- Evidence before claims; fail-closed (uncomputable check = FAIL); T+1; full-|dW|@6.4bps costs.
