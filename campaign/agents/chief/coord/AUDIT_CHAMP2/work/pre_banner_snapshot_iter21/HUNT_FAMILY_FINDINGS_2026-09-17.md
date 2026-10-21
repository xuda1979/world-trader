> **[ITER20 SUPERSEDE BANNER — 2026-09-18]** The champion of record is now the ITER20
> SR-max book: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv — ann 36.41% / SR 3.4551 /
> MDD -5.93% / 0 neg years / gross 1.6 exact (sha16 766fc0ce9926d793). Operator objective
> 2026-09-18: Sharpe-max subject to ann>=20% and gross<=1.6; the prior ann-max vintage
> (39.50 / 3.2176, ITER19) is archived byte-exact as archive_*_SUPERSEDED_by_ITER20_srmax.csv.
> Every earlier headline quoted in this document (39.50, 38.11, 37.49, 37.195, 40.84,
> 55.5, 62.4, ...) is SUPERSEDED history kept for provenance — it WAS current once, it is
> not current now.

# HTS-STYLE HUNT-FAMILY SWEEP — 2026-09-17
**Multi-agent hunt-family generator: seeking a genuinely NEW, decorrelated, gate-passing daily
engine to raise the champion's capital-real dAnn>0 (the champion is a concentrated energy book).**

## Method
Built `campaign/HUNT_HARNESS.py` — a pre-gated hunt harness enforcing the champion acceptance
battery from the start (standalone SR>=1.5, T+1 causal, full |dW| costs @ 6.4bps, ac1<0.5,
uniqR>=0.08, |corr-to-champion|<=0.4, mass-position, 0-negative-year bar). Each "agent" is a
distinct, genuinely-new tradable data surface (none are the champion's oil/nat-gas family).
Champion baseline for gating: ann 39.50% / SR 3.22 / MDD -6.52%.

## Hunt-agent results (all independent, reproducible)
| Agent | Surface (data) | Signal family | Best SR | corrC | Verdict |
|---|---|---|---|---|---|
| 1 | SPY put-call ratio (cboe_pcr) | PCR level z rev/mom | -0.29..-0.96 | ~0.0 | REJECT — no standalone edge |
| 2 | China-HK northbound flows (em_hsgt) | flow z mom/rev/own | 0.37..0.55 | 0.02 | REJECT |
| 5 | WB broad commodity CS mom (wb_commodity) | 21/63/126d cross-sectional | -2..-6 | 0.03 | REJECT (strongly negative) |
| 6 | Nat-gas storage (gas_storage) | storage draw/z | 1.43 (z_mom) | 0.06 | REJECT — under 1.5 AND within-energy (not decorrelating) |
| 7/9 | Gold-Silver ratio | **monthly spot artifact DEBUNKED**; honest GLD/SLV daily | 0.18 | ~0 | REJECT — no edge on tradable daily ETFs |
| 10 | China A-share CSI300 (cn) | 21/63/126d mom/rev | 0.77 (rev) | 0.11 | REJECT |
| 11 | Crypto breadth (coingecko) | -- | no data | -- | REJECT (data absent) |

## The one false-positive we caught (why rigor matters)
`wb_cmo` gold/silver appeared to give SR 2.5-3.4 with corr ~0.15-0.22. On inspection this is
**monthly World-Bank spot-index data (1 row/month), NOT a tradeable daily series**. Honestly
re-tested on daily GLD/SLV ETFs: **zero edge (SR ~0.18)**. This would have been a classic
sleeve-adoption artifact had it been taken at face value.

## Conclusion
Across every genuinely-new, tradable, decorrelated surface currently on disk that we screened,
**no engine clears the standalone SR>=1.5 + decorrelation + flatten-trap + dAnn>0 battery.**
This is a comprehensive, reproducible confirmation of ITER16's structural-frontier finding:
the champion's energy-complex edge (IR 2.8-3.0) is not matched by any currently-available
decorrelated family (IR ~0.5-1.9). The frontier is NOT a matter of "we haven't scanned the right
family" among existing data — it is a genuine per-gross-return gap (champion 21.2%/gross vs
decorrelated families sub-1.9 IR).

## What would actually move the needle (per the audit + this sweep)
1. **Genuinely NEW data that isn't on disk** — FX deposit-rate carry, full futures chains,
   intraday order flow / microstructure imports, or a new macro dataset with a HIGH per-gross
   return. The available suite is exhausted at the honest frontier.
2. **De-concentration as a risk-choice (not alpha)**: a 33%-brwt-cap variant trades ~2.6pp/yr
   ann for SR 3.42 / MDD -5.50% — a legitimate risk-reduced live deployment, documented in
   RESEARCH_AGENDA_2026-09-17.md.

## Files
- `campaign/HUNT_HARNESS.py` — reusable pre-gated hunt harness (kept for future hunt agents).
- `campaign/RESEARCH_AGENDA_2026-09-17.md` — prioritized plan (Tier1/2/3).
- This findings sheet.
