# SHARED HONESTY + GATES CONTRACT (all engine-hunt agents)
Every candidate sleeve MUST pass ALL of these (fail-closed). Log exact numbers in FINDINGS.md.
1. T+1 / no lookahead: signal at t uses data <= t; trade at t+1.
2. Costs: 6.4bps one-side on FULL |dW| traded notional (TRADE_RECORD_STANDARD) + borrow 0.5%/yr
   on short notional. If the instrument is an equity L/S book, model non-shortable stocks (a
   fraction of the bottom names can't be shorted -> their short leg must be dropped or costed).
3. Gates (ALL):
   a) FULL-window net SR >= 1.0 after costs (for a NEW sleeve to be champion-eligible).
   b) Param-plateau: chosen params on plateau (neighbors within 20% of peak SR).
   c) Halves: H1 SR >= 0.5 AND H2 SR >= 0.5.
   d) Yearly: <= 2 negative years each > -5% (track 0-neg separately for champion fit).
   e) Signal-scramble 200x: real SR > 95th pctile (p < 0.05).
   f) Decorrelation vs CHAMPION campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv:
      |corr| < 0.15 preferred; 0.15-0.35 mark "corr_ok_secondary".
   g) Vol-target ~10% ann trailing-only, scale clip <= 3.0.
   h) Economic rationale (2-3 sentences) in .meta.
4. Save per contract: campaign/scripts/{name}.py (reproducible) + sleeve CSV
   campaign/agents/chief/coord/<AGENT>/sleeves/{name}.csv [date,ret] + {name}.csv.meta
5. Honest negatives: log exact numbers (SR/negyears/corr/scramble) in FINDINGS.md and the
   DEAD_IDEAS.csv row via coordinator. Never force a pass.
