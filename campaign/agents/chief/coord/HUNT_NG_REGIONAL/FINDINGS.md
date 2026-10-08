# FINDINGS — HUNT_NG_REGIONAL (regional non-L48 natgas storage cross-section)

Date: 2026-10-08. Charter: `CHARTER.md` (pre-registered 18 configs, sealed
before any result; 16 in the driver run + 2 mirror configs completed same
session). Gates: `../GATES_CONTRACT.md` verbatim. Inputs: frozen disk
vintages, sha16-pinned in CHARTER.md (verified in-driver at load).

## VERDICT: HONEST NEGATIVE — no config clears the gates contract. Seam CLOSED.

18/18 pre-registered configs measured. Full table (SR / H1 / H2 / negY /
scramble-p):

| family | config | SR | H1 | H2 | negY | scram-p | gate outcome |
|---|---|---|---|---|---|---|---|
| F1 | follow_deficit_5y | 3.584 | 3.361 | 3.790 | 7 | 0.450 | FAIL d (7>2), FAIL e |
| F1 | fade_5y | -3.598 | -3.375 | -3.805 | 13 | 0.340 | FAIL sign+d+e |
| F1 | follow_deficit_4y | 4.191 | 3.888 | 4.483 | 6 | 0.925 | FAIL d (6>2), FAIL e (p=0.93!) |
| F1 | fade_4y | -4.204 | -3.901 | -4.496 | 13 | 0.010 | FAIL sign+d (mirror) |
| F2 | mom | 2.734 | 0.478 | 4.731 | 7 | 0.355 | FAIL b (H1 cliff 0.48 vs 4.73), d, e |
| F2 | rev | -2.768 | -0.515 | -4.765 | 13 | 0.730 | FAIL |
| F2 | mom_volnorm | -2.779 | -0.517 | -4.837 | 12 | 0.165 | FAIL |
| F2 | rev_volnorm | 2.742 | 0.478 | 4.800 | 4 | 0.675 | FAIL b, d, e |
| F3 | saltstress_1.5 | 0.005 | 0.000 | 0.007 | 2 | 0.210 | FAIL a (0.005 << 1.0) |
| F3 | saltstress_2.0 | 0.043 | 0.000 | 0.061 | 3 | 0.780 | FAIL a |
| F3 | saltstress_hyst | -0.082 | 0.000 | -0.115 | 4 | 0.375 | FAIL a |
| F3 | dispersion_long | 0.107 | 0.050 | 0.148 | 11 | 0.755 | FAIL a+d |
| F3 | dispersion_short | -0.114 | -0.059 | -0.154 | 12 | 0.985 | FAIL |
| F4 | raw_long | -0.568 | -0.707 | -0.433 | 9 | 0.055 | FAIL a+d |
| F4 | raw_short | 0.568 | 0.707 | 0.433 | 16 | 0.840 | FAIL a+d |
| F4 | z_long | -1.615 | -1.159 | -2.140 | 16 | 0.005 | FAIL sign+a+d |
| F5 | build_disp_long | 0.130 | 0.064 | 0.178 | 11 | 0.080 | FAIL a+d |
| F5 | build_disp_short | -0.142 | -0.079 | -0.190 | 11 | 0.170 | FAIL |

## Reading (honest)

1. **The expressible mechanisms are NULL.** F3 (salt-stress complex tilt,
   the only family with an economic-rationale prior for leading the price)
   and F5 (build-dispersion tilt) measure |SR| <= 0.14 across all variants.
   The regional storage stress states carry NO incremental price information
   on the complex beyond what is priced at the Thursday print. This is the
   direct regional analogue of row 57's L48 result ("fully priced at
   publication") and extends it: the cross-sectional dispersion is priced too.
2. **The high-SR F1/F2 rows are QUANTITY-BOOK ARTIFACTS, not tradable
   returns**: they mark storage-quantity z-convergence (physical mean
   reversion of gas-in-ground), not any tradable instrument, and they fail
   the contract's non-SR gates anyway (negY 6-13 vs <=2; scramble p up to
   0.93 — the 4.19 SR is statistically indistinguishable from shuffled
   quantity noise). Recorded as the implementability trap the charter's P4
   anticipated; NOT chased.
3. **P3 control confirmed directionally**: F4 residual is small and
   sign-unstable (raw +0.57/-0.57 mirrors, z form negative) — the L48-vs-sum
   residual carries no clean information (mostly revision noise).
4. **Predictions scorecard (sealed pre-run):** P1 correct (F1 fail, though
   the failure mode was gate-d/e not gate-a), P2 correct-with-qualification
   (salt stress was the best expressible family and still null), P3 correct,
   P4 correct (and stronger: the trap rows fail scramble, so even the
   inadmissible class is noise).

## Provenance / scope notes

- The 2010-01 floor is EIA's own publication limit for regional splits,
  verified live this session (dnav NW2_* starts 2010-01; API v2 monthly
  regional starts 2011-01; ir.eia.gov ngs history WAF-blocked). No longer
  history exists to extend the span. Re-measure trigger: EIA publishing
  pre-2010 regional history, or a licensed vendor panel.
- Per charter stop rule: seam CLOSED. A DEAD_IDEAS row records it. No
  second round on this seam without NEW data.
- Nothing outside this directory touched: no champion/weights/manifest/
  suite file modified; champion of record unchanged (cfa9ec4d38158691).

## Artifacts

- `work/hunt_ng_regional.py` — 16-config driver (reproducible; asserts input
  sha16s at load).
- The 2 mirror configs (F1_fade_4y, F2_rev_volnorm) ran in-session via the
  same functions (log above); numbers in the table.

HUNT_NG_REGIONAL DONE — honest negative, seam closed with exact numbers.
