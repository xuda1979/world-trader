# CHAMP_AUDIT_METRICS — statistical robustness audit of the champion

Target: `campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv` (champion of record,
ITER19 12-sleeve prune, rebuild via `campaign/scripts/rawew13v2_build.py::build()`).

**HEADLINE CORRECTION (honesty note):** the charter cites ann 39.50%/SR 3.22. The on-disk
champion of record today prints **ann 33.85% / SR 3.22 / vol 10.52% / MaxDD -6.52% / 0 neg
years, n=4806, 2008-03-31..2026-08-28** (eval.py). The ann delta (39.50 -> 33.85) is the
CAMP_COST R3 costfix (6.4 bps FULL |dW| one-side, no 0.5 half-turn) + T+1 causal re-emit +
ITER19 prune — i.e. the 39.50 figure was an undercharged predecessor. SR 3.22 matches.
All findings below are on the CURRENT, honestly-charged file.

Reproducibility first: `build()` reproduces the on-disk series to **max|diff| = 1.0e-16**
(byte-faithful at float precision). Static IS-fitted shares (SHRINK_D=0.98): brwt5 .1774,
brwt7 .1667, brwt10 .1663, C5ng .1087, C5ngsum .0989, diescrack .0926, a6r7 .0506, QAxasts
.0465, A5r2 .0346, dualmom .0334, carryv2 .0243, CFX4 0.

## 1. Block-bootstrap SR (3000 draws, 12-month blocks = 252 obs, circular, seed 20260914)
- Point estimate SR = 3.2176.
- **95% CI = [2.757, 3.942]** (median 3.264, mean 3.286, sd 0.297).
- P(SR < 2.0 goal) = **0.0000** (0/3000). P(SR < 1.66) = 0.0000; P(SR < 2.53) = 0.0017.
- Robustness: 63-day blocks give CI [2.790, 3.914], P(SR<2.0)=0.0000.
- vs prior CI [1.66, 2.53]: our CI lower bound (2.757) sits ABOVE the prior CI upper bound
  (2.53) — the champion SR is significantly above the prior generation, not inside it.
- VERDICT: **PASS — SR 3.22 holds decisively.**

## 2. Sub-window stability
| window    | ann     | vol    | SR   | MaxDD  |
|-----------|---------|--------|------|--------|
| 2008-2015 | 28.62%  | 8.58%  | 3.33 | -5.95% |
| 2016-2019 | 42.19%  | 9.39%  | 4.49 | -6.52% |
| 2020-2023 | 36.00%  | 14.71% | 2.45 | -4.94% |
| 2024-2026 | 33.33%  | 9.65%  | 3.45 | -5.48% |
- Halves: H1 SR 3.58 / H2 SR 3.02. No window collapses (min SR 2.45, 2020-2023, the
  high-vol COVID window); MaxDD never breaches -7% in any window.
- VERDICT: **PASS — stable across all four regimes incl. GFC and 2020.**

## 3. Negative-year margin
- **0 negative years out of 19.** Worst year **2013 +5.62%** (margin +5.62 pp), then 2021
  +7.84%, 2011 +9.64%.
- Extra stress: worst 252-day rolling window **+0.92%** (ended 2014-06-17) — even the worst
  12 months made money; worst month -2.46% (2022-08); worst day -4.60% (2026-03-17);
  26/222 negative months.
- VERDICT: **PASS on the stated gate** — but flagged: 19/19 positive years is extraordinary;
  see skeptic notes below.

## 4. Leverage & cost audit (rebuild-checked)
- Gross sum|w|: **exactly 1.600000000000 every day** (min=max=1.6, 0/4806 days off by >1e-9).
- Margin: max(1.6-1,0)*4.5% = **2.70%/yr** exactly, charged daily (1.0714 bp/day).
- Turnover (NAV rebalance layer): 0.003/day = **7,447 bp/yr one-side notional** = 0.75
  turns/yr; cost at 6.4 bps = **0.48 pp/yr**; p99 daily turnover 0.017, max 0.058.
- Sleeve-internal costs sit inside the sleeve CSVs at 6.4 bps FULL |dW| (costfix); margin +
  NAV-turnover are the only add-ons. Counting is honest; no 0.5-turn undercharge remains.
- VERDICT: **PASS — capital-real, exactly 1.6x, fully charged.**

## 5. MaxDD regime (-6.52%)
Top-3 drawdown episodes (peak -> trough -> recovery):
1. **-6.52%**: peak 2018-06-19 -> trough 2018-06-25 (4 trading days, not a 1-day crash),
   recovered 2018-07-20. Attribution: brwt10 -2.34pp, brwt7 -1.87pp, brwt5 -1.18pp.
2. **-5.95%**: 2008-12-16 -> 2008-12-19, recovered 2009-01-23 (brwt10 -1.48, brwt5 -1.24,
   brwt7 -1.11).
3. **-5.55%**: 2009-02-05 -> 2009-02-11, recovered 2009-02-27.
- So: yes, the headline MaxDD is a single short event window (6 calendar days, June 2018),
  BUT all three worst episodes are driven by the SAME brwt (Brent-WTI spread reversion)
  complex, which holds a median **78.4% of gross (max 90.0%)** and is internally +0.62..+0.84
  correlated. Effective number of sleeves (1/HHI): median 4.4, min 3.7.
- VERDICT: **PASS with caveat** — DD is shallow and fast-recovering, but the risk book is
  effectively ~4.4 slots with one family dominating. Diversification optics ("12 sleeves")
  overstate independence.

## Skeptic extras (not in charter, run for completeness)
- Skew 7.28 red-flag test: dropping the top 1/5/10/20 days *raises* SR
  3.22 -> 3.39 / 3.51 / 3.50 / 3.44. The SR is NOT carried by fat right-tail outliers
  (top-5 days: 2020-03-19 +17.7%, 2020-03-20 +14.0%, 2020-03-18/09 +5.8%, 2009-02-12 +5.1%);
  those days actually dilute Sharpe. Tail risk is on the LEFT and small (worst day -4.6%).
- Reconstruction/CX check: weights are T+1 causal (nav.shift(1)); max single-sleeve gross
  weight 0.53 (33% of book, 2017-08-18) — no hidden single-name bet beyond brwt block.

## VERDICT
**SR 3.22 / ann 33.85% is statistically robust as measured**: block-bootstrap CI [2.76,
3.94] excludes the 2.0 goal with probability 0/3000 and sits entirely above the prior CI
[1.66, 2.53]; all sub-windows SR >= 2.45; 0 negative years; costs and leverage honestly and
exactly charged. Residual skeptic concerns, ordered: (1) brwt-complex concentration (median
78% of gross — the book is one strong commodity-spread bet plus satellites); (2) 19/19
positive years and skew 7.28 imply an unusually smooth path — consistent with the seasonal/
event sleeves (C5ng, diescrack) whose edge is real per scramble tests but whose capacity/
regime-persistence is unknowable from price history alone; (3) headline ann is 33.85%, not
the charter's 39.50 — quote the honest number.

CHAMP_AUDIT_METRICS DONE

## ROUND 1 NUMBERED SUMMARY (charter items 1-5, in order)
1. **Block-bootstrap SR** — 3000 draws, 12m (252d) circular blocks: SR point 3.2176,
   95% CI [2.757, 3.942], P(SR<2.0)=0.0000 (0/3000); 63d-block check CI [2.790, 3.914];
   CI lower bound 2.757 > prior CI upper 2.53. VERDICT: PASS, SR holds decisively.
2. **Sub-window stability** — 2008-15: ann 28.62%/SR 3.33/MDD -5.95%; 2016-19: 42.19%/4.49/
   -6.52%; 2020-23: 36.00%/2.45/-4.94%; 2024-26: 33.33%/3.45/-5.48%. H1 3.58 / H2 3.02.
   No collapse; weakest is 2020-23 (SR 2.45, vol 14.7%). VERDICT: PASS.
3. **Negative-year margin** — 0 neg years / 19; worst year 2013 +5.62% (margin +5.62 pp),
   then 2021 +7.84%, 2011 +9.64%; worst 252d rolling +0.92% (2014-06-17); worst month
   -2.46% (2022-08); worst day -4.60% (2026-03-17). VERDICT: PASS (flag: 19/19 positive
   years is extraordinary; capacity/regime-persistence unknowable from history).
4. **Leverage & cost audit** — rebuild max|diff| vs on-disk = 1.0e-16; gross sum|w| exactly
   1.600000000000 all 4806 days (0 overshoot); margin 2.70%/yr (0.6 x 4.5%) charged daily;
   NAV turnover 7,447 bp/yr one-side = 0.48 pp/yr at 6.4 bps FULL|dW; sleeve-internal costs
   already in sleeve CSVs (costfix). Counting honest. VERDICT: PASS. NOTE: headline ann is
   33.85%, not the charter's 39.50% (costfix + T+1 causal + ITER19 prune); SR 3.22 matches.
5. **MaxDD regime (-6.52%)** — single short event window: peak 2018-06-19 -> trough
   2018-06-25 -> recovered 2018-07-20; top-3 episodes (-6.52% Jun-18, -5.95% Dec-08,
   -5.55% Feb-09) ALL driven by the brwt Brent-WTI complex (e.g. Jun-18: brwt10 -2.34pp,
   brwt7 -1.87, brwt5 -1.18) which holds median 78.4% of gross (max 90%); effective #sleeves
   median 4.4, min 3.7. VERDICT: PASS with caveat — one-family risk concentration.
Skeptic extra: dropping top 1/5/10/20 return days RAISES SR (3.39/3.51/3.50/3.44) — edge is
not tail-carried. OVERALL VERDICT: champion metrics (33.85% ann / SR 3.22 / MDD -6.52% /
0 neg yrs) are statistically robust; residual risk is brwt concentration, not statistics.
No sleeve CSV emitted — this agent is read-only per charter.
ROUND 1 DONE
