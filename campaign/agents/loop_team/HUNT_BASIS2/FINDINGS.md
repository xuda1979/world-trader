# HUNT_BASIS2 FINDINGS — cross-commodity basis/spread mean-reversion (2026-09-02)

Agent: loop_team/HUNT_BASIS2 (reassigned slot; prior HUNT_BASIS died on API 429 — its findings
do not exist; everything below is my own fresh work). All numbers recomputed by me from raw data;
harness = `scratch/lib.py` (mechanics mirror the frozen brwt engine, verified — see §1).

Champion correlation reference (charter): `campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv`,
sha256 72475976bc33c43a…, 4989 rows 2006-10-02..2026-08-27 (n=4575 on the 2008+ inner calendar with
my sleeves). NOTE: this file is the FIX variant (not truncated to 2008-03-31). For robustness I also
checked corr vs GOAL100_HONEST11_BALANCED (the audit-endorsed 4522-row champion): L40Z20 0.0525,
L15Z15 0.0674 — identical verdicts. HONEST11FIX vs HONEST11L16 BAL: corr 0.9999, max|diff| 0.0022.

## 0. VERDICT SUMMARY — 0 of the charter-gate sets fully PASSED; 2 sleeves delivered as NEAR-MISS
Two diesel-crack basis sleeves PASS 7 of 8 gates each and are the only genuinely new decorrelated
daily engines found; both fail the scramble gate AS WRITTEN (which is degenerate — see §3).
- diescrack_L40Z20: FAILS only scramble_p (0.575 vs required <0.05). PASS: SR 1.007≥0.6, H1 0.926,
  H2 1.118, neg-yr tolerance (1/19, worst -0.50%), |corr| 0.0516<0.15, ac1 -0.057<0.5, uniqR 0.159≥0.08.
- diescrack_L15Z15: FAILS scramble_p (0.540) AND neg-yr tolerance (2017 -6.48% < -5% floor).
- All other tested families: hard FAIL (§5). NO sleeve met all 8 gates → per charter, no candidate
  is claimed as a PASS. Both files delivered for the chair to adjudicate the scramble-gate defect.

## 1. HARNESS VERIFICATION (before any candidate was scored)
- Reproduced the proven E1_brwt_spread_rev15_2000 sleeve from raw FRED (brent, wti_full) with my
  lib (z15/±1.5, T+1 sp.diff().shift(-1), 6bps/side half-turnover, expanding vt 0.10 min60 cap3):
  SR 2.76 vs ref 2.76, ann 29.3% = 29.3%, MDD -7.9% = -7.9%, max|diff| 2.05e-04 (r1080 vs r1081
  interpolation on the vt input — cosmetic float noise, 1504/4560 rows >1e-6 all pre-2009).
  My cost convention (6bps/side on |Δpos|/2) reproduces the committed sleeve — confirmed against
  the committed generator campaign/scripts/backtest_brwt_spread_rev15.py + E1 detrunc script.
- Champion flatten stats: uniqR 1.000, ac1 -0.063 (healthy reference engine).
- Sanity on scramble null: literal permutation-scramble of the champion's returns hits "p≈0.78"
  — confirms (as VET_HONESTY already found) that a SR-based permutation null cannot fail a
  positive-SR series (SR is permutation-invariant). I therefore ran BOTH: (a) the charter's
  block-scramble as written (block-permutation, p(SR_perm≥SR_real)) and (b) the discriminating
  position-lag scramble (circular-lag the position series vs returns, 200x, lags 21..T-21).

## 2. DATA INVENTORY (verified on disk, not assumed)
- Futures CSVs: NONE for commodities. tools/quant/data/stooq_c5/ is EMPTY (0 files). polygon/ has
  only CL (an equity ticker 2024-07..2026-08, 13 rows — NOT WTI futures). twelve*/polygon_v2 hits
  (C, SI, NG, PL, ZS, CT…) are all equities (ZS=Nutanix $25-372; CTAS, SBUX, SBR…). No GC, HO, RB,
  LC, CT commodity futures anywhere.
- Daily spots available (harness FRED + newdata): brent 2000+, wti/wti_full 1986+, DHOILNYH
  (heating oil) 1986+, DHHNGSP/natgas 1997+, DJFUELUSGULF (Gulf diesel) 1990+, xau 2007-12+,
  slv 2006-09+, DCOILWTICO/DCOILBRENTEU dupes of wti/brent (mean|diff| 0.0, corr 1.0).
- ABSENT (charter items that could not be run): gold-platinum (no PL daily), copper-gold ratio
  (copper only MONTHLY: copper_monthly.csv, 415 rows), live-cattle-feed corn (no C/LC),
  soy-crush (no S/ZL). GASREGW + WTREGEN are WEEKLY (median gap 7d) — only usable with ffill.

## 3. THE SCRAMBLE GATE IS DEGENERATE AS WRITTEN (material, affects every past audit too)
"200x block-scramble p<0.05" — if p = P(SR_scrambled ≥ SR_real), then ANY positive-SR series
trivially passes (scrambled SR ≈ 0 < real). My L40Z20: p=0.575 by literal block-permutation yet
p=0.0000 under the position-lag scramble that actually tests signal alignment (SR collapses from
1.01 to scramble null). The committed sleeves' own meta (brwt15) used "shuffle positions vs
returns" = the position-lag version — i.e. the campaign has been running the meaningful test, but
the charter text describes the vacuous one. RECOMMEND: charter gate text → "200x position-lag
scramble p<0.05" (my implementation: circular shift of pos by uniform lag in [21, T-21]).

## 4. DELIVERED SLEEVES (near-miss candidates; files in sleeves/)
Diesel-crack basis = log(DJFUELUSGULF×42 gal/bbl) − log(wti_full). Mechanism: refining margin
reverts as utilization/runs respond; not present in the champion pool (champion holds crude-grade
basis brwt + NG weekday cycles, no product-crack engine).
Construction (both): z of log-spread vs trailing mean/sd, position ±1 when |z|>gate, T+1 P&L,
6bps/side on half-turnover, expanding vt 0.08 min60 cap3, borrow 0.5%/yr on the 1-unit short leg
charged on every nonzero row (incl. cost-only entry/exit rows → conservative), gate-off rows
exactly 0.0. Eval 2008-01-01+ (warmup only), n=4605, 2008-03-28..2026-08-10.

### diescrack_L40Z20 (lb=40, |z|>2.0) — sha256 e8a083dfba497735a8fa5aa4852758bd540c410bd5371ddfd0dfe203afc60b8d
| Gate | Value | Verdict |
|---|---|---|
| SR (2008+) | 1.007 (t=4.30, n=4605; SR_m 0.935) | PASS ≥0.6 |
| H1 / H2 | 0.926 / 1.118 | PASS |
| neg yrs | 1/19 (2013 -0.50%) | PASS ≤2, >-5% |
| block-scramble (literal) | p=0.575 | **FAIL** (<0.05 required; degenerate null, §3) |
| position-lag scramble | p=0.0000 | (real test: edge is signal alignment) |
| corr to champion | +0.0516 (n=4575); vs HONEST11 BAL 0.0525 | PASS <0.15 |
| ac1 / uniqR | -0.057 / 0.1594 | PASS <0.5 / ≥0.08 |
| ann(geo) / MDD | 7.82% / -9.07% | (informational) |
Robustness: T+2 extra-lag probe SR 0.69 (vs 1.01) — decays with lag, consistent with a real but
fast-decaying signal; IS(2008-2012) SR 0.58 / OOS(2017+) SR 1.07; costs+borrow drag SR 1.05→1.007
(0.04 SR; turnover 4.97%/day one-side = 0.75%/yr cost + 0.5%/yr borrow). Risk disclosure: signal-on
only 11.0% of days → active-day vol 19.3% (2.48× the 7.8% all-day vol); zero runs: 195 (longest 93d,
80 runs ≥20d) — by design, same convention as champion's brwt gates; 2020-04-20 negative-WTI print
(-36.98) makes log() undefined → that spread row drops (2-day bridge); 2020-03-30 +15.2% single-day
tail (largest). Corr to champion pool sleeves: brwt15 +0.137, brwt10 +0.138, C5ngsum -0.003,
QAxasts +0.087, carryv2 -0.024, dualmom -0.023. Blend diagnostic (ex-post, NOT a gate): 90/10
champion/L40Z20 → SR_d 4.128 (champ alone 4.072 on same n), MDD -4.77% — small but positive
diversification.

### diescrack_L15Z15 (lb=15, |z|>1.5) — sha256 4ee8c87cc768d309e4030de719f599ef7d21649954530aed16be331d21df6083
SR 0.962 | H1 0.980 / H2 1.001 | neg yrs 2/19 (2013 -2.23%, 2017 **-6.48%** → FAILS the >-5% floor)
| corr +0.0657 | ac1 -0.073 | uniqR 0.3587 | MDD -11.68% | ann 7.80% | literal block-scramble p=0.540
(FAIL), position-lag p=0.0000. Signal-on 24.2% of days. Delivered as the faster variant; strictly
dominated by L40Z20 on gates.

## 5. REJECTED FAMILIES (best config of each grid, all FAIL ≥1 hard gate)
| Family (best cfg) | SR | ann | MDD | negy | corr | Verdict |
|---|---|---|---|---|---|---|
| Gold-silver z-rev (lb40 g2.0) | -0.12 | -1.2% | -48% | 7 | +0.018 | FAIL (no edge; confirms E4/D-series) |
| Au/Ag ratio TREND (lb40) | +0.12 | +0.6% | -27% | 10 | -0.022 | FAIL SR |
| NG-WTI basis z-rev (lb15 g1.0) | 0.66 | 6.9% | -19% | 7 | +0.052 | FAIL negy (7) + SR<0.7 margin |
| NG-Brent basis z-rev (best 0.56) | 0.56 | — | -23% | 5-6 | +0.03 | FAIL negy+SR |
| HO-WTI gasoline…crack z-rev (lb15 g1.5) | 0.77 | 6.9% | -15% | 3 | +0.090 | FAIL negy (3>2); grid plateau SR 0.58-0.77 |
| WTI-Brent far-gate z-rev (lb15 g2.0) | 1.98 | 14.0% | -5.4% | 0/19 | **+0.320** | **FAIL corr (>0.15)** — same engine as champion brwt at wider gate; residualized vs all 4 brwt sleeves (betas 0.72-0.89): SR -2.84, corr -0.72 → pure factor re-dress, NOT a new engine |
| WTI-Brent spread MOMENTUM (all cfgs) | -0.8..-2.2 | — | ≤-46% | ≤27 | — | FAIL (spread mean-reverts, doesn't trend) |
| Pump-gasoline−WTI (GASREGW weekly ffill, DISCLOSED stale-lag) | 0.81 | — | -30% | 1 | +0.038 | FAIL SR (best 0.81 @ lb60); ffill basis risk |
| BW rev lb15 g2.0 corr detail | 1.98 | corr 0.32 to champion — the ONLY high-SR hit of the session is the champion's own engine family | | | | |

## 6. HONESTY NOTES
- T+1: all P&L via sp.diff().shift(-1) — signal at t uses info ≤t only; T+2 probe reported.
- Costs: 6bps/side charged on half-turnover in-series (not post-hoc); turnover reported exactly.
- Borrow: 0.5%/yr charged on the short leg on all nonzero rows (overcharges cost-only rows →
  conservative). No rebate credited.
- No flattening: gate-off rows are genuine 0.0 (position genuinely off); nonzero-constant-run max
  = 0 for both delivered files; uniqR ≥0.159.
- Regenerability: sleeves regen from raw CSVs via scratch/lib.py to max|diff| 1e-16 (pandas float
  repr differs in last ULP; values identical). Metas disclose full recipe.
- NOT verified / disclosed basis risk: FRED spots are roll-free proxies; the tradeable instrument
  (HO-CL futures calendar) carries roll/basis risk not modeled here; DJFUELUSGULF is an EIA Gulf
  spot (0 gaps>3d since 2008 — clean daily). Single-day tail +15.2% (2020-03-30) means DD-based
  gates understate tail risk (same caveat L16_AUDIT raised for brwt).
- C5ng family: my faithful reimplementation of the committed NG weekday cycle scored SR 1.63 /
  corr 0.248 to champion (vs committed C5ng corr ~0.19 pool claims) — close but not identical to
  the committed sleeve files (different data cleaning + vt 0.08 vs 0.10); committed files taken as
  given, no new evidence against them.

## 7. BOTTOM LINE FOR THE LOOP
The only untapped decorrelated daily engine found in the on-disk universe is the diesel-crack
basis (L40Z20: SR 1.01, corr 0.05, 1 neg yr, 7/8 gates). If the loop adopts the position-lag
scramble definition (which is what the committed sleeves were actually validated with), L40Z20
is a legitimate new sleeve (small: ~7.8% ann at vt 0.08, adds ~+0.06 SR to the champion at 10%
weight in the diagnostic blend). If the literal block-permutation text stands, it must be
recorded as REJECT (p=0.575). No gold-silver/copper-gold/ags work was possible: no data on disk.
HUNT_BASIS2 DONE
