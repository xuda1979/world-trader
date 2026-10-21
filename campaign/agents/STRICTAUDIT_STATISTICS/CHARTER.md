# STRICTAUDIT_STATISTICS — adversarial statistical robustness of SR 5.24 & 0/19 negative years (read-only)

TARGET: GOAL100_STRICTTRADE_BALANCED_daily.csv claims SR 5.24 (daily) / 3.46 (monthly), MaxDD -6.1%,
0/19 negative years, OOS 2017+ 55.9%, LOYO 46.7-51.0%, monthly-SR bootstrap CI [3.02,4.01].

YOUR JOBS (statistical adversarial review — the headline numbers are impressive; find the fragility):
1. SOURCE OF THE SHARPE: SR 5.24 daily is enormous for any real strategy. Decompose it —
   how much is (a) high mean, (b) low vol (vt10 targets 10%), (c) negative autocorr of daily
   returns (mean reversion inflates daily SR vs monthly), (d) the 12-engine diversification?
   Compute the NEGATIVE-AUTOCORR penalty: resample daily returns by BLOCK (e.g. 21-day blocks,
   252-day blocks) so autocorr is destroyed; recompute SR. Report the block-bootstrap SR — this
   is the honest Sharpe an investor who can't capture daily mean-reversion would get.
2. 0/19 NEGATIVE YEARS CREDIBILITY: individual sleeves have negative years (XGB1y worst -13%,
   a6r7 -4%, carryv2 -1%, A5r2 -1.9%, QAxasts -3.7%, dualmom -4.3%). Yet the blend claims 0/19.
   Verify this is statistically plausible, not a vol-target artifact: do a drop-one-year exercise
   and a leave-one-sleeve-out. What if the two weakest sleeves (lowest standalone SR) are dropped?
3. DROP-ONE SENSITIVITY: compute the blend WITHOUT each single sleeve (construct EW-of-11 via
   the documented pipeline if reproducible, else a simpler equal-vt blend proxy) — report ann/SR/DD
   delta per omission. Is any sleeve a keystone (large positive delta) = concentration risk, or
   a drag (increasing when removed) = hidden overfitting? XGB1y was -10pp keystone in the old
   16-pool — does that hold in the 12?
4. OVERFITTING / SELECTION: the 12 sleeves were selected from ~330+ tested ideas (GOAL100). The
   exponents SELECTED the best survivors. Apply a multiple-testing lens: with 330 independent
   candidates you'd expect some impressive-but-false survivors by chance. Is the residual
   "49.4%" after all audit removals likely real edge or selection-adapted overfit? Do a
   splice/scan robustness: split OOS into 2017-21 vs 2022-26 — is the edge stable or decaying?
   Annual SR by year for the blend (list SR per calendar year).
5. BOOTSTRAP CIs: reproduce monthly-SR CI [3.02,4.01] and also daily-SR CI. Report whether the
   lower bound comfortably clears the "SR>=2" goal and whether the CI width signals real vs luck.
6. TAIL RISK: distribution is hugely right-skewed (e.g. 2023 +151%, 2020 +91%). This is a
   few-event-driven return. What fraction of total return comes from the very best single years
   and single days? If the top-1, top-5, top-10 days are removed, what is the honest ann/SR/DD?
   Is the "0/19 negative years" dependent on the black-swan right tail?
7. 3-YEAR SUBWINDOW DDs: re-verify every 3y-window DD <= -6.1% and LOYO 46.7-51.0% if reproducible.

Write campaign/agents/STRICTAUDIT_STATISTICS/FINDINGS.md with exact numbers and an honest bottom
line: what SR / what 0-neg-year claim is defensible AFTER autocorr & tail corrections? Is the
system robust or lucky? Last line exactly: STRICTAUDIT_STATISTICS DONE
