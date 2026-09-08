# RES_REVERSAL — short-horizon cross-sectional reversal engines
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Find >=1 NEW decorrelated DAILY engine from short-horizon CROSS-SECTIONAL reversal across the
WIDE equity panels. The champion is momentum/style-heavy (dualmom, QAxasts, XGB1y) — reversal is
the natural decorrelated complement (corr to momentum typically strongly negative).

## Data (verify yourself)
- tools/quant/data/twelve_big (298 names OHLCV) + twelve_extend (440 names).
- tools/quant/data/kenfrench/ (if needed for cross-sectional factor construction).
- Sector ETFs (more_etf/) for sector-relative reversal.

## Ideas
- 1-5 day cross-sectional reversal: rank returns over trailing window, short winners/long losers,
  with shortability handled (drop non-shortable bottom names per ai-devops).
- Sector-relative reversal (vs sector beta), dollar-neutral, vol-targeted.
- WARNING: KF industry mom/rev FAILED before (C1 best 0.35); reversal must be strong enough to
  clear SR>=1.5 net at 6bps — test the low-turnover tail (rebalance every few days).

## FIRST STEP
`python3 campaign/team/lib/corr_gate.py <cand.csv> 0.15` — reject if |corr| to champion >= 0.15.

## Gates (ALL, via campaign/bt/)
SR>=1.5 net; H1/H2>=0.5; <=2 neg yrs >-5%; 200x block-scramble p<0.05; |corr|<0.15 to champion;
T+1; 6.4bps/side full |dW|; borrow + shortability modeled; flatten ac1<0.5 & uniqR>=0.08.

## Deliverable
Sleeve CSV + .meta + thin repro under campaign/team/agents/RES_REVERSAL/sleeves/. REJECT-with-numbers ok.

## Done marker
Last line of FINDINGS.md exactly: RES_REVERSAL DONE
