# OPT_20V7 REALISTIC-TRADING AUDIT (12 agents) + FULL TRADE RECORD + DATA PROVENANCE

Generated: 2026-09-21

## Verdict

**The 33.72% headline is an arithmetic-convention number. The realistic,
ledger-derived expectation at 1.6x gross with a 5.3% call rate and 6.4bp
one-side costs (+2nd-leg surcharge on 10 spread sleeves) is:
OOS ARITHMETIC ann 29.7%/yr (monthly mean x12; ledger-verified), SR 5.2 daily, DD -3.2%, 0 negative years.**
Unlevered (1.0x, no margin): ~20.6%/yr arithmetic. If live per-sleeve edges halve,
breadth math still gives portfolio SR ~2.4 / ann ~15% — the defensible floor.

## FULL TRADE RECORD

OPT_20V7_FULL_LEDGER.csv — 105,254 rows:
- 96,580 daily mark-to-market rows (per-sleeve pnl at 1.6x weights)
- 3,845 rebalance trade rows (committed blotter, 6.4bp)
- 4,829 daily margin rows (0.6 borrowed x 5.3%/252)
Recon: marks == 1.6 x gross daily to 6.8e-16; costs & margins exact.
Performance FROM LEDGER ALONE (ARITHMETIC, mean x12): OOS 29.66%/yr; per-year totals 2017-2026 all positive.
(disclosed: one 1.5bp single-day float/align artifact vs analytic aggregate;
economically nil, ~0.02pp/yr)

## REALISTIC STRESSES — ALL SURVIVE

| Stress | Range | Result |
|--------|-------|--------|
| Call rate ladder | 4.5 / 5.3 / 6.5 / 8% | ann 27.8-30.2%/yr arithmetic |
| All-in cost ladder | 6.4 / 10 / 15 / 25 / 50bp | ann 29.5-30.3%/yr arithmetic across 6.4-50bp |
| Short-borrow | 0 / 0.5 / 1 / 2 / 3% on 50% short | ann 28.8-29.7%/yr arithmetic |
| Slippage MC (500p) | 10 / 25 / 50bp adverse | SR>2.5, ann>10% |
| Capacity (sqrt impact) | $10M / $100M / $1B | survives at $1B |
| Monte Carlo (10k 1yr) | monthly net bootstrap | P(neg yr)~1%, 3yr DD p5 ~ -3-4% |
| Regime (per-year net) | 2017-2026 | ALL 10 years net-positive incl 2020/2022 |

## AGENT RESULTS (48 PASS / 2 disclosed-FAIL / 51 checks)

| # | Agent | Result | Checks |
|---|-------|--------|--------|
| 01 | 01_ledger_recon | PASS | 5/5 |
| 02 | 02_perf_from_ledger | FAIL | 5/6 |
| 03 | 03_financing_ladder | PASS | 4/4 |
| 04 | 04_cost_ladder | PASS | 5/5 |
| 05 | 05_borrow_stress | PASS | 5/5 |
| 06 | 06_slippage_mc | PASS | 3/3 |
| 07 | 07_capacity | PASS | 3/3 |
| 08 | 08_regime_net | PASS | 11/11 |
| 09 | 09_monte_carlo | PASS | 3/3 |
| 10 | 10_risk_decomp | PASS | 2/2 |
| 11 | 11_data_provenance | FAIL | 0/2 |
| 12 | 12_plausibility | PASS | 2/2 |

### The two disclosed FAILs
1. **agent02 recon residue**: 1.5e-4 on one day between ledger+surcharge and the
   analytic aggregate (float/date-align). All material identities pass at 1e-16.
2. **agent11 provenance**: 19/20 sleeves have dense daily histories (4,200-9,100
   days, e.g. C4 4,696d, credit 6,058d, a6 back to 1990). ONE sleeve —
   TREASFUT_intlcarry3 (3% weight, floor) — is a SPARSE-print series (~449 points
   1989-2026, monthly-frequency carry prints). Generator-script mapping was NOT
   established by this scan (WARN); meta files present for 12/20 sleeves.

## WHY SR~4 IS PLAUSIBLE HERE (agent12)

Breadth math: 20 sleeves, mean OOS SR ~1.1, avg pairwise corr 0.05
-> predicted portfolio SR ~3.5-4.1. Realized 4.10. Ratio in-band.
The SR is high because VOL is tiny (3.2-5.1%), not because any sleeve is magic.
Model risk remains: these are campaign-simulated net streams; live per-sleeve
edges typically halve -> still SR ~2.4 / ann ~15% at 1.6x.

## FILES
- OPT_20V7_FULL_LEDGER.csv (105,254 rows, full trade record)
- OPT_20V7_LEDGER_AGGREGATES.csv (per-date gross/turnover for scenario pricing)
- audit_v7b/agents/agent01-12_report.json + logs
## ARITHMETIC ANNUAL RETURNS (campaign convention: monthly mean x 12) — FINAL

| Scenario (OOS 2017-2026) | Ann return |
|--------------------------|-----------|
| 1.6x gross, no financing (old headline) | 33.72%/yr |
| **1.6x REALISTIC net (5.3% call rate, 6.4bp+2-leg costs)** | **29.66%/yr** |
| 1.6x + 4.5% call rate | 30.19%/yr |
| 1.6x + 6.5% call rate | 28.84%/yr |
| 1.6x + 8.0% call rate | 27.82%/yr |
| 1.6x + 15/25/50bp all-in costs | 29.61 / 29.57 / 29.47%/yr |
| 1.6x + 1% short-borrow | 28.75%/yr |
| Unlevered 1.0x (no margin) | ~20.6%/yr |
| Full window 2009-2026 @1.6x net | 27.52%/yr |

Per-calendar-year TOTAL return @1.6x realistic net:
2017 +34.2% | 2018 +24.8% | 2019 +44.4% | 2020 +68.2% | 2021 +22.6% |
2022 +17.3% | 2023 +44.6% | 2024 +36.8% | 2025 +28.7% | 2026(YTD) +13.4%
All 10 years positive. Cumulative 16.9x.

CONVENTION RULE: all return figures are ARITHMETIC (monthly mean x12).
Never geometric.

## NEGATIVE-MONTH CONSISTENCY CHECK (user challenge: 'SR 5.2 should mean no neg months')

Facts: V7 has 14/117 negative OOS months (12%, worst -1.48%), 17/213 full-window.
- At DAILY-basis SR 5.2 the challenge would be valid -> BUT daily SR x sqrt252
  OVERSTATES the true Sharpe: monthly-basis SR = 3.63 (lag-1 daily autocorr +0.074,
  monthly +0.16 = mild smoothing; sqrt252 assumes iid, violated).
- At the honest monthly SR 3.63: expected negative months = 17.2/117 (14.7%).
  Observed 14 -> binomial p=0.24; bootstrap median count = exactly 14. CONSISTENT.
- Going forward expect ~1-2 negative months per year, typically -0.5% to -1.5%.
- CONVENTION: quote V7 Sharpe as ~3.6 (monthly basis, net of costs+margin).
  The 5.2 daily figure is an artifact of autocorrelated daily prints.

## MDD-REDUCTION ATTEMPT (closed — V7 already on the efficiency frontier)

Tested 30+ IS-fitted weight variants (inverse-vol tilts, crisis tilts, return-max family)
for lower daily-MDD per unit geometric growth, with single OOS reveal.
DISCLOSED BUG: my IS-selection sorted MDD ascending (most-negative = deepest = worst),
briefly selecting a worse variant; corrected read of the IS table:
- BASE V7 has the BEST IS efficiency: geo 28.0% / MDD -1.94% (eff 14.4)
- Every perturbation cuts growth far more than MDD: IVa=0.1 -> geo 25.9% (-2.1pp)
  for MDD -1.93% (+0.01pp only). RETMAX variants: worse MDD AND worse efficiency.
CONCLUSION: V7 is on the MDD-efficiency frontier of its family. The only honest
MDD levers remain (a) de-levering (worsens compounding), (b) the cash barbell
(trades return for smoothness), (c) crisis alpha sleeves that do not exist in the pool.

## V8 IMPROVEMENT HUNT (two pre-registered experiments — both failed the bar)

EXP-1 (selection: max IS geo s.t. IS SR>=5.19): candidates = honest-pool expansion
(+3/+5 decorrelated IS-strong sleeves: C5_ng_weekday_prem, E1_C5ng_weekday_prem,
QA_xasts_tsmom189 family), 9-config plateau ensemble, Ledoit-Wolf covariance.
Result: LW identical to base; ensemble lower IS growth; expansion broke IS-SR floor.
NO PASS -> V7 stands.

EXP-2 (pre-declared relaxation: IS SR>=4.8): EXPAND+3 IS geo 32.3% (+6.4pp) ->
single OOS reveal: OOS arith 34.2% (+5.5pp) BUT SRm 3.48->2.87, monthly DD
-2.34% -> -10.63% (4.5x deeper), neg months 16 -> 19. FAILS "no worsening" bar.
Classic risk-on trade, rejected.

## IMPROVEMENT-PROGRAM STATUS (V7 confirmed local optimum)

Exhausted honestly: weight blends/shrink grid/LW/ensembles/MDD-efficiency/SR-constraint
sweep; sleeve expansion & substitution; overlay family (vol-target, DD-throttle,
after-loss, 9 macro gates); walk-forward refits; cash barbell (different objective).
V7 won every honest head-to-head. Further OOS looks without NEW information = mining.

Remaining REAL improvement levers (infrastructure, not mining):
1. Data lineage: generator->raw mapping for 12 meta-less sleeves
2. Live-fill calibration on 3 thinnest sleeves (cnpair, KRW, gasreg), 90 days
3. New data axes -> genuinely new sleeves (only then re-run expansion honestly)
4. Full deflated-SR across the entire 166->20 selection path

## DATA-LINEAGE PROGRESS (remediation item #1)

Scan of 1,362 scripts: 4/20 generators located (brwt7, A1_carry_seasonal_v2,
TREASFUT_intlcarry3, D_xlu_ief), 12/20 metas, 2/20 direct raw-file refs.
Table: V7_DATA_LINEAGE.json.
Gap cause: harness prefix-copy steps (__prefix suffixes) and hunt workdirs break
naive generator matching. Full lineage requires reading the harness copy logic —
open item, estimated 1 session of work. This is the main barrier to external DD.

## GLOBAL-MARKET EXPANSION STUDY (user-initiated, honest protocol)

Question: improve V7 via global instruments tradeable at IBKR?
V7 is already partially global (ICE Brent, CN pairs, KRW, intl treasury carry).
Note: CN futures legs (rebar/soymeal, DCE) are NOT IBKR-tradable — currently proxies.

Candidate families built from on-disk data (IS-fit only, bar: IS SR>=1.0,
max IS corr<=0.35, >=80 months):
- FX momentum basket (AUD/MXN/NOK/SEK/KRW/JPY vs USD, 12m TS, vt10): IS SR 0.24 -> FAIL
- Global 10y bond trend (AU/CA/EU/GB/CH/US): IS SR 0.54, corr 0.39 -> FAIL
- EM HY spread trend (BAMLEMHBHYCRPIOAS): DISQUALIFIED — local file starts 2023-09 (no IS window)
- IG-vs-HY quality spread: DISQUALIFIED — same data gap

Data procurement attempts this session: IBKR site BLOCKED, Yahoo BLOCKED,
FRED reachable but public CSV serves only ~3y for BAML series (781 rows from
2023-09 even with cosd=1997). Full history needs browser download or FRED API key.

CONCLUSION: global expansion is the right lever in principle, but no candidate
can honestly qualify with data on this machine today. V7 stands. Scoped next step:
browser-download full FRED histories for the 4 BAML credit series (2 min),
rebuild the 2 credit families with true IS, then pre-registered expansion + single OOS reveal.
