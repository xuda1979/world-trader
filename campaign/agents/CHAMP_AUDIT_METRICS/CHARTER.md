# CHAMP_AUDIT_METRICS — statistical robustness / metrics audit of the CURRENT champion (read-only)

Target: results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv (ann 39.50%/SR 3.22).
Path: the build is campaign/scripts/rawew13v2_build.py; sleeves in the POOL; rebuild with build().

Your job: stress the headline METRICS (not the code) — would a skeptic kill the champion's stats?
1. Block-bootstrap the daily SR: 3000 draws, 12m blocks (match the campaign convention). Report
   the 95% CI. Does the SR point estimate hold? Compare to the 2.0 goal and to prior CI [1.66,2.53].
2. Sub-window stability: slice 2008-2015 / 2016-2019 / 2020-2023 / 2024-2026 and report ann/SR/MaxDD
   each. Flag any window where SR collapses or MaxDD spikes.
3. Negative-year margin: compute the WORST calendar year return and the distance to 0 (the 'every
   year >= 0' gate). Report the margin in pp and the top-3 worst years with years.
4. Leverage & cost audit: confirm capital-real gross is EXACTLY 1.6 daily (sum|w|, 0 overshoot),
   margin 2.70%/yr, turnover in bp/yr. Confirm counting is honest.
5. MaxDD regime: is -6.52% driven by a single short event window? Report the worst 3 drawdown
   peaks-to-troughs with dates.

Output: FINDINGS.md with a metrics table + verdict on whether the 39.50/SR3.22 is statistically robust.
Last line: CHAMP_AUDIT_METRICS DONE
