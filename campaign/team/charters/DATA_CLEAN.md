# DATA_CLEAN — fail-closed cleaning & lint of every series
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Every dataset consumed by any backtest must pass a fail-closed lint before use. You own that
check for ALL tools/quant/data/ families (esp. any new one a RES_* agent wants to use).

## Lint battery (write as small TDD-tested functions, reuse bt/align where possible)
- span: min span (>= 2006 for champion-eligible, disclose if shorter); start/end sane.
- rows: n > 0; date column monotonic, no dup dates.
- gaps: max_gap_days <= 5 for daily (disclose/flag > 5); fill only where model economics allow.
- NA/Inf: report count; drop or flag — never silently pass.
- plausibility: OHLC sanity (high>=low, close within day range), value domain (e.g. VIX 0-100+,
  SKEW 90-180), unit check (pct vs decimal vs bps — the C2 fly 100x bug).
- flatten gate: ac1<0.5, uniqR>=0.08 when a daily series is meant to be daily.

## Deliverable
- A cleaned/linted dataset OR a clear REJECT with exact failing metric in FINDINGS.md.
- A manifest.csv row per series with every lint field.
- Never mutate the raw file: write cleaned copy to the family dir as <name>_clean.csv.

## Rules
- Clean+lint logic must be TDD (failing test first). Fail-closed: uncomputable lint = fail.

## Done marker
Last line of FINDINGS.md exactly: DATA_CLEAN DONE
