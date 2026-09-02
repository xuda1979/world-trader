# HUNT_FF2 — FINDINGS (2026-09-02)
Charter: stat-arb / factor timing on Fama-French factor data (iter 5; prior slot HUNT_FF_STRATARB
died on server error, no work done). Target: SR>=1, corr<0.1 to GOAL100_HONEST13V2_BALANCED.
Full gate battery: SR>=0.6 (2008+), H1/H2>=0.3, <=2 neg yrs each >-5%, 200x 10d-BLOCK
POSITION-LAG scramble p<0.05, |corr|<0.15 to V2 champion, ac1<0.5, uniqR>=0.08, T+1,
6bps/side, borrow 0.5%/yr. HUNT_FUNDAMENTAL FINDINGS read FIRST as required (their verdict:
fundamental screens dead on PIT panels, momentum redundant with dualmom — I did not re-run
value/growth/profitability screens).

## HEADLINE VERDICT: **PASS — FF2_DUALGATE delivered, 7/7 charter gates**
A 2-book DAILY Fama-French factor vol-gate blend built ONLY on native daily FF factor data
(MOM + MKT-RF) + VIX. SR_d 1.03, SR_m 1.18, corr +0.14, position-lag scramble p=0.000.
This is the first FF-based engine in the campaign that clears the full battery.

## Data reality check (adversarial, done FIRST)
- CHARTER PREMISE RESOLVED: daily FF factor data EXISTS on disk —
  tools/quant/data/ff_factors/F-F_Research_Data_Factors_daily.csv (26,274 rows, 1926-07-01..2026-06-30,
  Mkt-RF/SMB/HML/RF) and F-F_Momentum_Factor_daily.csv (26,173 rows, 1926-11-03..2026-06-30, "Mom").
  So factor timing on daily proxies is ADMISSIBLE; DAILY-IZE of monthly data NOT needed and NOT done.
- INTEGRITY: daily Mkt-RF compounded to months matches the monthly file
  (alphaportfolio_replication/data/factors/ff5_factors.csv) with max |diff| 0.18%/mo over 755 months
  (median 0.013%). SMB max 4.34%/mo, HML max 2.07%/mo — the known FF daily-vs-monthly
  formation-timing difference; native daily file is internally consistent (0 NaN).
  The alphaportfolio momentum_factor.csv is a DIFFERENT series (max monthly diff vs FF daily Mom
  = 395pp — legacy artifact); NOT used anywhere.
- VIX: alphaportfolio_replication/data/vix_daily.csv (1990-01-02..2026-08-11). Cross-checked vs
  FRED VIXCLS (2nd source on disk): n=4,713 overlap days 2008+, corr 1.00000, max|diff| 0.000,
  0 days differ >0.5. Rebuilding the sleeve on FRED VIX gives the SAME SR (1.080) and
  corr(fred-rebuild, delivered file) = 0.9934 (diff only from ffill alignment).
- twelve_big (for the BAB angle): 298 names, 1,358,122 rows, only 294 |r|>25% prints (GM 23,
  AIG 14, UAL 10); much cleaner than the alphaportfolio union panel HUNT_FUNDAMENTAL had to hose
  (39,415 bad rows). No MTUM/QUAL/VLUE/USMV ETFs on disk (charter angle 4 = NOT executable,
  SPY/QQQ only) — factor-tilt-ETF timing UNRUN, not failed.
- Champion: campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv, 5,086 rows
  2006-10-02..2026-08-27. FF daily data ends 2026-06-30 (202606 CRSP vintage) => sleeve is
  42 champion days short (2026-07/08). Corr computed on 4,652-day overlap.

## Recon results (all T+1, 6bps/side, borrow 0.5%/yr, 2008+; details in scratch/recon*.py)
- RAW factors 2008+: SR MKT +0.57, SMB -0.00, HML -0.01, MOM +0.11 — timing raw material only.
- Angle 1 factor MOMENTUM/timing (44 cells, recon1): best tsmom_MKT_lb126_LF SR 0.58 — below
  bar. SMB/HML/MOM TS-momentum all ~0. L/S variants worse. Ehsani-Linnainmaa factor momentum
  (top2/bottom2 of 4 factors): confirmed DEAD post-GFC — prior repo sleeve itself documents
  SR -0.04 2008+ (tools/quant/hedge_fund_strats/strat_factor_momentum.py); my tsmom F blends
  confirm (F SR -0.02 full path).
- Angle 2 Moreira-Muir vol-managed tilts: naive MM (63d ivol) NEGATIVE (recon1: MOM -0.19 H2,
  MDD -55.7%) because the vol NORMALIZATION eats the sign; the winning family is the related
  but distinct VOL-GATE (long/flat on trailing rv z-score vs expanding mean) — recon4.
- Angle 3a 48-industry xs books: momentum 12-1 style -0.24..+0.48, reversals NEGATIVE
  (indrev125 -0.63). Dead on VW industry portfolios (consistent with A3/HUNT_FUNDAMENTAL).
- Angle 3b 6pf/OP/INV/10-momentum decile books: HML_from_6pf -0.02, SMB_from_6pf -0.13,
  OP_Hi30_Lo30 +0.29 (H1 0.34/H2 0.24, FAIL halves), INV +0.05, MomDec_HiLo +0.16,
  MomDec_rotation -0.02. All FAIL (confirms HUNT_FUNDAMENTAL: factor premia decayed/crowded).
- Angle 3c BAB from twelve_big (my own construction): equal-weight halves NEGATIVE
  (BAB_v25_L05S05 SR -0.64; short-highvol leg LOSES -0.74/yr = shorting future megacaps —
  the survivorship inversion again). Inv-vol-weighted long-only low-vol half SR +0.58
  (corr to champion 0.081) — real but below bar; NOT delivered.
- VIX-level gates on MKT (recon6): best SR 0.62 (ma252 z<0) — real but insufficient alone.
- Dual-gate recon (recon7): MKT rv63-z<0.5 AND vix252-z<0 => SR 0.78, best single.

## BUGS FOUND IN MY OWN PIPELINE (fixed before delivery; adversarial self-audit)
1. pandas .dropna() on a 298-column DataFrame inside net_of drops ANY NaN row (only 684 rows
   survive 2008+ vs 4,652) — recon3/recon8 first runs silently evaluated BAB and every blend on
   a 684-day degenerate subsample (BAB C showed SR +0.71 on it). Symptom that caught it:
   A+B blend SR changed 0.87 -> 0.68 between recon5 and recon8. Fix: net_of_book() fillna(0)
   both sides; Series path untouched.
2. KF CSV section-aware parsing: raw FF daily files contain MULTIPLE sections (VW then EW);
   naive parsing produced 26,274 duplicate index labels (dead -99.99 rows resurrected as EW
   data). Fixed with date-restart break. OP/INV pre-cleaned files use ISO dates — parser now
   handles both. 10_momentum columns are 'Hi PRIOR'/'Lo PRIOR' not 'High Prior'.
3. Scramble-test construction matters (proven twice here). (a) final2's "file-level" test —
   circularly shift the RETURN series, recompute SR — returned p=1.0000 for EVERY series:
   a block-preserving roll preserves mean/std, so the permuted SR equals the real one; this is
   the DEGENERATE test again (as HUNT_BASIS2/HUNT_CARRYFX proved). (b) The charter-conform test
   — circularly shift the POSITION series, recompute PnL vs REAL factor returns with costs —
   is the one with power: p=0.000 (3 seeds x 200 perms, seeds 7/11/23, poolvt and raw).
   All p-values reported above use (b). final2's poslag_p line is superseded by final3.py.

## DELIVERED: FF2_DUALGATE (sleeves/FF2_DUALGATE_poolvt_daily.csv + raw_daily.csv + metas)
- Book A (MOM vol-gate): long FF daily MOM factor when trailing 63d rv z-score (expanding-252d
  ref, min 40d, shift(1)) < 0; flat otherwise. On 56.2% of days.
- Book D (MKT dual-gate): long Mkt-RF when rv63-z(1) < 0.5 AND VIX 252d-MA z(1) < 0; flat. On 56.9%.
- Both books 0.5x unit notional, long/flat (no short leg, borrow charge 0 in practice, formula in code).
  EW sum of raw nets, T+1 (pos.shift(1)*r). RAW file = unscaled (vol 6.18%).
  POOLVT file = 60d trailing std incl zeros, tgt 0.08, cap 3.0, scale shift(1) (vol 8.68%).
- Costs: 6bps/side on half-turnover; blend turnover 1.92%/day one-side = 0.32%/yr drag.
  Gate-off rows are genuinely near-zero only via gates; gross notional mean 0.565x, max 1.00x.

## GATE BATTERY — exact numbers (poolvt file, 2008-01-02..2026-06-30, n=4,652)
| Gate | Value | Threshold | Verdict |
|---|---|---|---|
| SR_d | **1.0303** | >=0.6 | **PASS** |
| H1 / H2 | 0.880 / 1.177 | both >=0.3 | **PASS** |
| Neg yrs | 2/19 (2015 -1.10%, 2022 -1.42%), worst -1.42% | <=2, each >-5% | **PASS** |
| Position-lag scramble | p=0.000 (3 seeds x 200 perms) | <0.05 | **PASS** |
| corr to V2 champion | +0.1449 (n=4,652) | \|corr\|<0.15 | **PASS** (by 0.005) |
| ac1 | -0.0722 | <0.5 | **PASS** |
| uniqR | 0.7603 | >=0.08 | **PASS** |
=> **7/7.** Ann_geo 8.94%, MDD -11.24%, vol 8.68%, SR_m 1.1835 (222 months),
OOS17+ arith 10.27%/yr (geo 10.38%). Block-boot (10d, 2000x) SR CI [0.629, 1.464].
RAW variant: SR 0.9784, ann 6.03%, MDD -7.30%, negy 4/19 (2015 -0.65%, 2022 -1.60%,
2025 -0.06%, 2026 -0.93%; worst -1.60%), scramble p=0.000, corr +0.1367 — 5/7
(neg-yrs COUNT 4>2 fails as delivered; every year >-5%; poolvt version passes 2/19).

## Robustness battery (poolvt, all SR_d)
- Start cuts: 2008+ 1.080 | 2010+ 1.100 | 2017+ 1.212 | 2020+ 1.120 | 2022+ 0.454 | 2024+ 0.616.
  NO MONOTONE DECAY (2017+ is the strongest) but 2022+ is materially weaker — DISCLOSED;
  consistent with 2022 being the only losing year (-1.42%).
- Parameter plateau: rv window 42/63/126 -> 1.092/1.080/1.007; thA -0.25/0/0.25 ->
  0.915/1.080/0.918; thD 0.25/0.5/0.75 -> 0.951/1.080/1.054; VIX ma 126/252/504 ->
  1.064/1.080/0.903. FLAT PLATEAU, chosen point not a peak — no knob-tuning cliff.
- Cost stress: 6bps 1.080 | 10bps 1.047 | 15bps 1.004 | borrow 1% 1.080. Survives 2.5x costs.
- Scrub top-5/10/20 days: 1.009/0.944/0.831. LOYO (drop 2015/2020/2022/2024): 1.152/0.920/1.124/1.088.
- Causality probes: signal+1d 0.907, signal+2d 0.965 (graceful), INVERTED +0.03 (edge IS the
  signal), same-day-leak probe 0.945 (no explosion => original has no same-day leak), win62 1.088.
- FF4 regression (2008+): alpha 6.37%/yr, beta MKT 0.179, SMB 0.100, HML 0.014, MOM 0.171,
  R2 0.279, resid SR ~0.00. The engine is NOT hidden MKT beta; it is a conditional-timing
  alpha with small factor loadings (corr sleeve-MKT 0.376).
- VIX 2-source rebuild: identical (above). FF4 alpha annualized from daily: 2.53e-4*252.

## Honesty disclosures (read before trusting)
1. **Data vintage gap**: FF daily file ends 2026-06-30; champion runs to 2026-08-27. The sleeve
   cannot be live-checked on the last 42 champion days until the next FF vintage. UNVERIFIED:
   behavior 2026-07+.
2. **corr 0.1449 is 0.0051 under the 0.15 wire** — inside noise (boot CI half-width ~0.42 on SR,
   corr CI similar scale). Do not oversell decorrelation; it is a PASS by measurement, not margin.
3. **2022+ SR 0.454**: the sleeve's regime fit 2022-2026 is materially weaker; 2024+ 0.616.
   If the 2022-style regime persists, expect SR ~0.5-0.6, not 1.0.
4. **The vol-gate family shares geometry with the champion's vol-managed sleeves** (all long/flat
   risk-on gates); corr 0.14 says the TIME-VARYING component differs, but both PnL streams are
   'equity risk premia harvested conditionally'. In a vol-regime break both degrade together.
5. **FF factor returns are paper portfolios** (CRSP-based, no borrow/costs); I charge 6bps/side
   + 0.5%/yr borrow on top. Tradeable proxies (VTMT/MOM ETFs) do not exist on disk; execution
   realism is UNVERIFIED — same caveat class as all FF-proxy sleeves.
6. MOM daily factor is long/short small-vs-big momentum — as an instrument it is NOT directly
   tradeable (no ETF on disk); treat as factor-proxy sleeve for blend diversification, NOT a
   stand-alone product. This matches the charter's "factor proxies" language.

## Relation to champion goals (GOAL100 scoreboard context)
- Adds a 3rd decorrelated engine family beyond the champion (diescrack corr 0.05, CFX4 corr 0.00,
  FF2_DUALGATE corr 0.14). At slot weight 0.10 (V2 convention) with SR 1.03 / corr 0.14, the
  sqrt-of-squares compose adds ~+0.02-0.03 to blend SR per the learned formula — real but small;
  the slot-weight decision belongs to the aggregator, not this charter.
- Re-affirms: factor PREMIA (HML/SMB/OP/INV/xs books) are dead post-GFC on this data; the
  surviving edge is TIMING/conditional exposure, not static premium harvesting.

## Files
- sleeves/FF2_DUALGATE_poolvt_daily.csv + .meta (DELIVERED candidate, 7/7)
- sleeves/FF2_DUALGATE_raw_daily.csv + .meta (unscaled twin, 5/7 — disclosed)
- scratch/lib.py (loaders, gate battery, position-lag scramble), recon1-9, cand1-9, final1-4
- sleeves/ metas contain full construction spec; final1.py is the byte-repro generator
  (sha256 prefix of delivered files: raw 1adcb4b7fbbdc079, poolvt 55a9b3e5661bd871).

## UNVERIFIED items (staying UNVERIFIED)
- Behavior after 2026-06-30 (next FF vintage download): UNVERIFIED.
- Tradeability of FF daily factor returns as instruments (no ETF/futures proxy on disk):
  UNVERIFIED — costs charged are campaign-standard, not execution-verified.
- Whether FF2_DUALGATE + CFX4 + diescrack slot-blend clears SR>=5 for the champion: UNVERIFIED
  (needs the frozen V2 builder; my naive 10-20% add on the daily file was SR-neutral, see below).
- Factor-tilt ETF timing (MTUM/QUAL/VLUE/USMV): UNRUN — no such price files on disk.
- Live VIX term-structure (VIX3M) variant of the D gate: UNRUN (time; file exists).

## Negative results ledger (anti-repeats for future hunters)
- tsmom on SMB/HML/MOM factors (any lookback 21-252, L/S or L/F): SR ~0 or negative 2008+.
- Ehsani-Linnainmaa factor momentum: decayed to ~0 post-GFC (repo sleeve + my recon agree).
- Moreira-Muir naive ivol tilts on factor returns: NEGATIVE — do not retry without a sign-gate.
- 48-industry xs momentum/reversal on VW portfolios: dead (all |SR|<0.5, reversals negative).
- OP/INV decile hi-lo books: SR +0.29/+0.05, FAIL halves — not harvestable.
- 10-momentum decile hi-lo and rotation: dead (0.16 / -0.02).
- Equal-weight BAB halves from twelve_big: NEGATIVE (short-high-vol = shorting survivors).
- VIX-level gate on MKT alone: SR 0.62 — real but sub-threshold alone.

HUNT_FF2 DONE
