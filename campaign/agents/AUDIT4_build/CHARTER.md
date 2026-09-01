# AUDIT4_build — adversarial audit of the champion construction (read-only)

champion_build.py builds the champion from sleeve files. Try to BREAK the math:
1. UNIT TESTS with synthetic sleeves where the answer is analytically known:
   a) 1 sleeve, constant return r: vt scale should converge to 0.10/0 (capped 8) — verify.
   b) 2 sleeves, zero corr, vt10: blend vol should be ~10%/sqrt(2) pre-global-vt.
   c) throttle: feed an equity curve with a known 126d drawdown — verify the throttle
      triggers exactly when trailing DD < -THR and the shift(1) prevents same-day action.
   d) costs: verify turnover accounting on a hand-computable weight path.
2. CODE AUDIT: check every line for lookahead: rolling(...).std().shift(1) everywhere?
   EW denominator counts sleeves not yet started (dilution) — confirm conservative not
   inflationary. Throttle trigger uses eq.shift(1)/rm-1 — confirm no same-day.
3. CONSTRUCTION invariants: weights sum: EW of vt-scaled sleeves = portfolio in 16 equal
   capital sleeves each internally vol-targeted — confirm no hidden leverage beyond the
   per-sleeve vt caps; report the implied gross exposure path statistics (mean/max of
   sum of per-sleeve |scale|/16).
4. REPRO: run champion_build.py --verify and champion20y_build.py --verify; confirm
   byte-identical; then perturb one input sleeve by +1bp on one day and confirm the
   output changes (sensitivity is alive, not cached).
Write campaign/agents/AUDIT4_build/FINDINGS.md with all test outputs. Last line: AUDIT4 DONE
