# HUNT_FXDEPO FINDINGS — FX deposit-rate & cross-rate carry engines (GOAL100 loop iter 6, 2026-09-03)

Agent dir: campaign/agents/loop_team/HUNT_FXDEPO/ (scratch/ = code, sleeves/ = deliverables).
All numbers recomputed this session from raw files. Reference blend = GOAL100_HONEST14V3_BALANCED
(committed; my loader: SR_d 3.923, ann 43.1%, MDD -4.92%, 0 negy on its own file — consistent
with the iter5 close). Prior FX findings (FXMICRO, CARRYFX, BASIS2) read first; dead variants
not re-run (list in §8). Gates per iter6 charter: SR>=0.6 (2008+), H1/H2>=0.3, <=2 neg yrs each
>-5%, 200x 10d-BLOCK POSITION-LAG scramble p<0.05, |corr|<0.15 vs HONEST14V3_BALANCED, ac1<0.5,
uniqR>=0.08, T+1, 6.4bps/side round-trip-equivalent (6bps/side here; campaign files use 6bps
convention = CARRYFX/BASIS2), borrow 0.5%/yr.

## 0. BOTTOM LINE
- **DATA: the charter's named domain "FX deposit rates" DOES NOT EXIST on disk.** No foreign
  deposit/policy/3mo rates, no LIBOR/EURIBOR/SOFR files, no forward points (grep §1). Only US
  DGS3MO daily (1981+) and MONTHLY 10y for 7 countries (2018+, 97-102 rows). True PIT carry
  accrual across countries is UNCONSTRUCTIBLE on this disk. Charter idea 3 = **BLOCKED**
  (consistent with FXMICRO G3 carry SR 0.23 and CARRYFX §6 tilt +0.004 using the 10y proxy).
- **DELIVERED (NEAR-MISS candidate, NOT a PASS): sleeves/FXD1_KRWTRI_raw_daily.csv** (+poolvt
  variant) — 3-book DEX cross z-reversion (KRW/SEK, KRW/CHF, KRW/NOK), lb(21,63) avg, cap 2.
  **SR_d 0.870 (0.6 gate PASS), H1 1.075/H2 0.606 PASS, 200x 10d-block position-lag scramble
  p=0.000 (seeds 0/1/2) PASS, ac1 -0.014 PASS, uniqR 1.000 PASS, corr to champion +0.005 PASS,
  corr to CFX4 +0.129 — 6/7 gates. FAILS the yearly gate: 8/19 negative years (worst -3.09%
  2018; ALL > -5%).** No regime/vol/rate gate I tested fixes the year count without killing SR
  (§6). Delivered for chair review, not claimed as champion-eligible.
- Marginal value at champion level (§7): w=0.10 raises champion SR_d 3.923→3.957 (vt variant
  3.990), SR_m 3.866→3.907, cuts MDD -4.92%→-4.48%/-4.66%, keeps 0 neg years — a real but small
  decorrelation/diversification win at ~4.5% ann cost, same shape as CFX4's marginal table.
- **G10-only Scandi crosses are DEAD (SR -0.141, 12 neg yrs): the KRW leg is the edge carrier.**
  The book's PnL is 2008-crisis-weighted (2008 +18.7%, 2009 +17.9%; top-10 days all in
  2008-09..2009-01 or 1998 crisis rows) — disclosed concentration.

## 1. DATA VERIFICATION (fail-closed, on disk)
- DEX crosses: 13 series in tools/quant/data/newdata/ (BZ, DN, IN, JP, KO, MX, NO, SD, SF, SI,
  USAL, USEU, USUK), all ending 2026-08-21, 4665-4666 rows from 2008-01-01, max gap 5 calendar
  days (weekend), zero Sat/Sun rows. Stale prints (0.0% return days) 2008+: KO 1.4% (max run 4d),
  IN 3.1%, others ≤0.9% — mild, and zero-print-filtered rerun barely moves SR (0.870→0.804, §5).
  newdata/ has DEXSDUS+DEXDNUS; the harness FRED dir lacks SD/DN (only SEUS vs SDUS naming:
  both checked) — I used newdata/ throughout.
- Deposit/short rates: DGS3MO 1981+ (n=11247), DGS1MO 2001+, DGS6MO 1981+, us2y 2000+. FOREIGN:
  NONE. grep for depo|euribor|libor|sofr over data dirs = 0 hits. Foreign rates on disk are
  10y MONTHLY only: au/ca/ch/ez/gb/jp/nz10y, 2018-01..2026-06, 97-102 rows each. **Idea 3
  BLOCKED for any true carry design**; the only PIT-runnable variant (10y-diff sign, EW
  JPY/CHF/EUR/GBP vs USD 10y, 2018+ window n=1952) scored **SR -0.530 (rising-diff)** /
  **+0.471 (level-diff)** — both fail every gate (and n is 8.5y). CLOSED, not iterated further.
- Price-path/instrument note for the audit (charter requirement): the delivered engine trades
  synthetic crosses KRW/SEK (mean 132.99, range 87.20-252.08 KRW per SEK), KRW/CHF (mean
  213.08), KRW/NOK (mean 141.02), reconstructed as DEX quotients; execution would be KRW NDF
  (offshore) + SEK/NOK/CHF spot. Top-10 |daily PnL| days (trade-record anchors): 2008-10-30
  +5.049%, 2008-10-10 +4.101%, 2008-10-07 +2.660%, 2008-10-08 +2.564%, 2008-10-16 +2.279%,
  1998-08-28 +2.148%, 2009-01-02 +2.101%, 1998-07-28 +2.047%, 2008-11-04 +2.015%,
  2008-09-18 +2.009%.

## 2. IDEA 1 — DEX cross z-reversion books (charter idea 1)
- Panel: 12 DEX series 1999-01-04..2026-08-21 (n=6930 common). Return-corr matrix: the Scandi/
  EUR block is highly correlated (DN/EUR -0.981, SD/EUR -0.816, NO/SD +0.805); EM block
  uncorrelated to it.
- Full spread grid (all corr>0.3 pairs × lb 21/42/63), per-book net SR 2008+: best is
  **KRW/SEK lb21 SR 0.784** (MDD -11.0%), then KRW/SEK lb42 0.684, KRW/CHF lb21 0.651,
  KRW/SEK lb63 0.639, KRW/CHF lb42 0.646, KRW/NOK lb21 0.513. NOTHING else >0.32. Full table:
  scratch/s1_grid_results.csv.
- **6/19 negative years even for the best single book** — the annual gate was always the issue,
  not the SR. 8 neg yrs for the 3-book EW (KRW3): 2013 -0.64, 2014 -1.73, 2015 -0.18, 2017
  -2.72, 2018 -3.09, 2020 -2.42, 2025 -0.91, 2026 -2.25 (%). Every one > -5% but 8 > 2.
- Gate variants on KRW/SEK lb21 (cap 1.0/1.5/2.0 × z-gate 0/0.5/1.0/1.5): SR 0.53-0.81, best
  cap1.0 gate0 — no z-threshold gate helps. Plateau flat (cap plateau for KRW3: 1.0→0.861,
  1.5→0.871, 2.0→0.870, 2.5→0.866; lb(21)→0.854, (63)→0.782, (21,63)→0.870, (21,42,63)→0.854).
- 6-book all-Scandi+KRW EW: SR 0.563; 4-book: 0.702; G10-only 6-book (SD/SF/NO/DN pairs):
  **SR -0.141** → KRW carries the edge. Single books: KO/SD 0.761, KO/SF 0.691, KO/NO 0.531,
  SD/SF -0.094, SD/NO -0.294, NO/SF 0.203.

## 3. IDEA 2 — cross-rate TRIANGLE books on the twelvedata majors
- 21 synthetic crosses (AUD/EUR/GBP/NZD/CAD/CHF/JPY), 2019-06-12..2026-08-05 common window
  (n=1936), z-rev lb 21/42/63: **ALL NEGATIVE SR** (scratch/s4_grid.csv). Best of 75 configs:
  AUDJPY lb63 **-0.093**; the liquid JPY/CHF/CAD crosses are worst (GBPJPY -1.33, EURJPY -1.35
  at lb63). Corr to champion ~0.02 (irrelevant — no edge). **CFX4's 4 books are the ONLY
  z-reversion spreads in the major-FX space with an edge; there is no untouched triangle.**
- Harness validation: my rebuild of CFX4 4-book dual-tf on raw closes = SR 2.407, corr +0.9984
  to the committed CFX4 sleeve (max|diff| 0.0166 — the committed file's extra vol scaling, per
  CARRYFX's own disclosure). My engine/mechanics match the lineage.
- Single-pair USD z-books (8 pairs × lb 21/42/63/dual): best EUR_GBP lb42 SR 0.653, H2 0.37 —
  below 0.6 and that pair is ALREADY a CFX4 book (family dedup). All USD pairs ≤0.16 or negative.

## 4. IDEA 3 — deposit-rate carry: BLOCKED (see §1). Novel rate-gate variants tested instead
   (PIT DGS3MO): EM-basket long when us3mo-z<0 (+thr variants): SR -0.32..-0.47; USD-vs-basket
   on 21d/63d rate-change sign: SR -0.08/-0.50 (gated: -0.10/-0.30). ALL NEGATIVE. The
   "dollar-smile / rate-momentum" family is dead on this data.

## 5. FXD1_KRWTRI — FULL GATE RESULTS (exact; raw variant = primary deliverable)
n=4666, 2008-01-02..2026-08-21, no zero rows, vol 4.24%, ann_geo 3.66% (arith 3.69%),
MDD -10.2%, max|day| +5.05% (2008-10-30), skew +2.61.
| Gate | Value | Verdict |
|---|---|---|
| SR (2008+) | 0.870 | PASS ≥0.6 |
| H1 / H2 | 1.075 / 0.606 | PASS ≥0.3 |
| neg years | 8/19, worst -3.09% (2018), all >-5% | **FAIL** (≤2 required) |
| 200x 10d-block position-lag scramble | p=0.0000 seeds 0,1,2 (real SR 0.870) | PASS <0.05 |
| ac1 | -0.014 | PASS <0.5 |
| uniqR | 1.000 | PASS ≥0.08 |
| corr to HONEST14V3_BALANCED | +0.005 (n=4665) | PASS <0.15 |
- poolvt variant (expanding vt 0.08 cap 8 shift1): SR 0.852, ann 8.9%, MDD -23.8%, negy 8 —
  2017 -6.57% and 2018 -7.38% ALSO break the >-5% floor. Strictly dominated; kept for the table.
- **Dedup**: corr(FXD1, CFX4) = +0.1292 (n=1723 common 2019+ window) — under 0.15, and the
  DATA DOMAIN (EM/Scandi DEX vs twelvedata majors) is disjoint; family relatedness disclosed.
- Cost/exposure decomposition: turnover 33.5%/day one-side (max 2.70), cost drag 5.07%/yr,
  borrow 0.53%/yr; gross exposure mean 0.696x, max 1.000x — no hidden leverage. KRW NDF
  cost-realism caveat: 6bps/side is optimistic for KRW NDF + 2-leg cross execution; at 15bps
  the book's 5.07% drag becomes ~12.7%/yr → net ann ≈ -3.9% — the sleeve does NOT survive
  realistic NDF costs. (SR at 15bps ≈ 0.15.) Disclosed as the main tradability risk.
- T+1 honesty: positions shift(1); T+2 probe (extra lag) SR 0.019 — edge decays with lag
  exactly as a fast mean-reversion should; same-day alignment corr +0.479 proves the shift
  matters (no same-day leak in the delivered file).
- Robustness: scrub-k SR 0.876/0.817/0.718/0.563 (k=5/10/20/50 — no single-day dependence);
  LOYO min 0.706 (ex-2009), max 0.952; IS(2008-15)-picked lb(10,21,42) full-window SR 0.869
  (same 8-negy verdict); OOS16+ 0.530, OOS17+ 0.624, OOS20+ 1.130, OOS23+ 1.202 (recent regime
  BETTER); zero-print-day filter 0.804.

## 6. NEG-YEAR-GATE RESCUE ATTEMPTS — ALL FAIL
- Spread-vol gate (63d vol >/< 252d median, ×0.75..1.25): SR 0.35-0.68, negy 6-9. No.
- DGS3MO z gate (z<0.5/1.0/-0.5, z>-0.5/0.5/1.0): best usz<1.0 SR 0.687 but H2 0.22 FAIL and
  negy 8. No config gets negy≤2 with SR≥0.6 and halves≥0.3.
- Book-count/dedup: 4- and 6-book EW variants have MORE neg years (9). No.
**The 8-neg-year structure is intrinsic: this book earns ~3.5-4%/yr in trend years and bleeds
1-3%/yr in grind years. It is a crisis-harvester, not an all-weather engine.**

## 7. MARGINAL VALUE AT CHAMPION LEVEL (blend champ*(1-w) + FXD1*w; champ alone SR_d 3.923,
SR_m 3.866, ann 43.1%, MDD -4.92%, 0 negy)
| w | variant | SR_d | SR_m | ann | MDD | negy |
|---|---|---|---|---|---|---|
| 0.02 | raw / vt | 3.930 / 3.940 | 3.875 / 3.885 | 42.2 / 42.4% | -4.83 / -4.85% | 0 |
| 0.05 | raw / vt | 3.940 / 3.962 | 3.887 / 3.910 | 40.9 / 41.2% | -4.70 / -4.74% | 0 |
| 0.10 | raw / vt | 3.957 / 3.990 | 3.907 / 3.939 | 38.6 / 39.3% | -4.48 / -4.66% | 0 |
| 0.15 | raw / vt | 3.973 / 4.001 | 3.926 / 3.950 | 36.4 / 37.4% | -4.27 / -4.73% | 0 |
Reading: +0.03..+0.08 SR_d and MDD relief at 0.7-5.7% ann cost. Same direction as every prior
FX/vol sleeve: raises SR, lowers ann — does NOT close the ann≥80 gap. CFX4+FXD1 EW (common
window): SR 2.045 vs CFX4 alone 1.897, MDD -5.74% vs -9.53% — genuinely complementary vol.

## 8. DEAD/BLOCKED LEDGER (do not re-run)
- BLOCKED: true deposit-rate carry (no foreign short-rate/forward data on disk; §1).
- DEAD (tested here, exact SRs above): DEX per-ccy momentum lb10-252 reb1/5 (best -0.02, gross
  NEGATIVE -1.9..-14.3%/yr — not a cost artifact); EM basket z-rev lb10/21/42 (-0.61..-0.80);
  Scand basket z-rev (-0.23..+0.01); G10-only Scandi 6-book (-0.141); us3mo level/change gates
  on EM or USD (-0.08..-0.50); 10y-diff carry sign (+0.47 level / -0.53 rising, both <0.6);
  21 synthetic major crosses z-rev (75 configs, ALL ≤-0.09); single-pair USD z-books (≤0.65);
  short-horizon per-ccy mom/rev lb2/3/5/10 (-0.28..-0.98, gross negative).
- Inherited-dead, NOT re-run (per charter): FXMICRO G1 Parkinson range-harvest, G2 open-close
  reversal, G3 10y-proxy carry, weekday holds; CARRYFX carry-tilt (+0.004) & Monday conditioning;
  BASIS2 gold-silver/NG-WTI/pump-gas families; DTWEXBGS momentum (SR 0.07-0.35, coord_emfx).

## 9. HONESTY DISCLOSURES
1. FXD1_KRWTRI is a NEAR-MISS: 6/7 gates, fails yearly-count 8/19 (each >-5%). Per charter I
   do NOT claim a champion-eligible PASS.
2. H.10 noon buying rates are reference prints, not executable quotes; +1 extra-day probe SR
   0.019 shows the edge is execution-lag-sensitive — real NDF fills at T+1 exist but with
   wider spreads than 6bps (15bps kills it: net ann ≈ -3.9%). Tradability UNVERIFIED.
3. Crisis concentration: 2008+2009 = half the PnL; max|day| +5.05%. The book is long
   crisis-reversion in KRW crosses; 2022-type regimes also pay (+14.5%) but grind years bleed.
4. My champion-file reload (SR_d 3.923 vs committed 3.92) matches the iter5 close; blend
   arithmetic above uses my in-memory reload, not the builder.
5. Scramble-gate note (inherited from BASIS2/CARRYFX): I implement the DISCRIMINATING
   position-lag block-scramble (10d blocks, positions rolled vs fixed returns, costs charged),
   not the vacuous returns-permutation. All scramble p's here use that definition.

## 10. WHAT WOULD CHANGE MY VERDICT
- A real daily deposit-rate/forward-point dataset (BBA/ICAP-style or central-bank policy rates)
  would un-BLOCK idea 3 properly.
- If the loop relaxes the yearly gate to "neg years >-3% each" (dd-tolerant), FXD1_KRWTRI_raw
  becomes a full 7/7 PASS and is immediately usable at w≈0.05-0.10 for the SR/DD benefit.
- A cheap KRW-NDF execution study (actual bid/ask) would settle the 6bps question.

## 11. FILES
- sleeves/FXD1_KRWTRI_raw_daily.csv + .meta (PRIMARY near-miss), FXD1_KRWTRI_poolvt_daily.csv
  + .meta (vt variant).
- campaign/scripts/fxd1_krwtri.py — frozen repro (byte-identical, max|diff| 5e-13).
- scratch/: lib.py (harness), s1_grid.py(+results.csv), s2_mom.py, s2b_cost_diag.py,
  s3_carry.py, s4_trirx.py(+s4_grid.csv), s5_eurusd.py, s6_variants.py, s7_ratez.py,
  s8_krwsek.py, s8b_gatebattery.py, s9_dedup.py, s10_ratediff.py, s11_final.py, s12_idea4.py,
  s13_final_audit.py, s14_negyr_diag.py, s15_mswb.py, s16_marginal.py, s17_oos.py,
  s18_v3corr.py, s19_instr.py, s20_warmup.py, s21_data_audit.py, s22_krwcop.py.

HUNT_FXDEPO DONE
