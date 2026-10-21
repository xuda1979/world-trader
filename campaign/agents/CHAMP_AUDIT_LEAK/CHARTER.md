# CHAMP_AUDIT_LEAK — adversarial causality/lookahead re-audit of the CURRENT champion (read-only)

Target-of-record: the RAWEW13v2 WEIGHTED champion — results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
(also at campaign/results/), built by campaign/scripts/rawew13v2_build.py. Current headline ann 39.50%
SR 3.22 MaxDD -6.52% 0-neg at capital-real gross 1.6.

Your job: TRY TO BREAK the causality/lookahead guards with fresh, independent methods (do NOT
assume prior audits are correct).
1. Same-day-leak forensics: reconstruct the per-day weights Wg from build() (nav.shift(1)) and
   compute corr(dW_t, r_t) across the full span and per-year. The committed T+1 book must show
   corr ~0 (the leaked book showed 0.78). Report the actual numbers.
2. Extra-lag probe: rebuild the champion but shift each sleeve input by an ADDITIONAL day (use
   the same build logic) and confirm ann/SR fall or stay ~flat (a signal that "trades on today's
   close" should be destroyed by an extra day's lag; if it IMPROVES by a lot, flag it).
3. Zero-run / flat-region forensics on the 12 sleeve inputs: read each sleeve CSV and the
   construction code for interior zero-runs; confirm each is strategy-by-design (band gates,
   long-flat), NOT missing data.
4. Cross-check a random 30 rows of the committed daily CSV against an independent recompute via
   build() (must match to ~1e-12; report max|diff|).

Output: campaign/agents/CHAMP_AUDIT_LEAK/FINDINGS.md — verdict + exact numbers.
VERDICT LINE: PASS or FAIL (with the weakest finding).
Last line: CHAMP_AUDIT_LEAK DONE
