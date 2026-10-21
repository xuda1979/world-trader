# HUNT_CROSSASSET2 FINDINGS — cross-asset relative books (GOAL100 loop iter 6, RELAUNCH, 2026-09-03)

Agent dir: campaign/agents/loop_team/HUNT_CROSSASSET2/ (scratch/ = code+results, sleeves/ = deliverable).
Reference blend = GOAL100_HONEST14V3_BALANCED (committed; my reload SR_d 3.940 on 2008+ window — consistent
with iter5 close 3.92 full-window). Conventions: T+1 (pos.shift(1)), 6.0bps/side on |Δw|/2 **per leg**
(FXD1-frozen per-leg accounting; verified byte-identical rebuild of FXD1_KRWTRI: corr 1.00000,
max|diff| 5e-13), borrow 0.5%/yr on shorts, no leverage (per-book gross ≤ 1.0). Gates (iter6 charter):
SR≥0.6 (2008+), H1/H2≥0.3, ≤2 neg yrs each >-5%, 200x 10d-BLOCK POSITION-LAG scramble p<0.05 (3 seeds),
|corr|<0.15 vs champion, ac1<0.5, uniqR≥0.08.

## 0. BOTTOM LINE
- **NO champion-eligible engine found. Charter families 2 (rates steepener) and 3 (credit-OAS) are DEAD
  on this data; family 1 (sector-basket) produced one NEAR-MISS: SEC3_sector_trio (6/7 gates, fails the
  yearly gate 8/19 — every neg year > -3.7%). Delivered sleeves/SEC3_sector_trio_zrev_daily.csv + .meta
  + campaign/scripts/sec3_sector_trio.py (byte-identical rerun verified, SR 0.6669) for chair review
  ONLY, per the FXD1 precedent. No PASS claimed.**
- Hunt cost: ~600 screened configs across 3 families; every number below recomputed this session from
  raw files. DEX cross z-reversion (partial-run) NOT redone per handoff (max SR 0.27, weak; FXDEPO
  concluded 8-negy intrinsic on that family).

## 1. DATA VERIFICATION (fail-closed; instrument+price paths recorded per charter)
- **Sector ETFs (REAL prices)**: tools/quant/data/twelvedata/{XLE,XLB,XLF,XLI,GLD,IEF,TLT,HYG,LQD,AGG,
  SPY,QQQ,DIA}.csv — 'close' col, 2006-09-26..2026-08-12 (HYG from 2007-04-11, LQD from 2006-10-13).
  **XLK/XLY/XLP/XLU/XLV/XLRE/XLC/XLK-family NOT on disk** (grep over twelve_big/twelve_extend/
  twelvedata/polygon_v2) — the charter's "XLE/XLB vs XLK" pair is only half-constructible; I used the
  4 available SPDR sectors. zero-ret frac 2008+ 0.5-1.7% (mild staleness). twelve_big has XLF only,
  twelve_extend has NO sector ETFs, stooq_c5/ is EMPTY, alpha_vantage/ empty.
- **DATA-QUALITY FLAG (twelvedata XLF pre-2010)**: 2008 has 54 |ret|>5% days (XLB 22, XLI 11, SPY ~22
  at 41% ann vol vs XLF-file 71% ann vol), incl 2008-07-16 +13.10% while XLB +0.38%/XLI +2.30%/SPY
  +2.45% same day, and alternating ±5-6% days 2008-07-08..22. Suspected stale/split prints in source.
  Impact bounded: SEC3 scrub5/10/20 SR 0.591/0.513/0.450 (no single-day cliff), and dropping XLF
  entirely (XLB-XLI alone) gives SR 0.239 — the basket, not one print, carries it, but tradability of
  the pre-2010 portion is disclosed as UNVERIFIED.
- **Rates curve (REAL daily yields)**: hedge_fund_strats/data_fred/{DGS1,DGS2,DGS5,DGS7,DGS10,DGS20,
  DGS30}.csv — n=4667 rows 2008-01-02..2026-08-27, zero NaN, max gap 4 calendar days. t10y2y 2005+.
- **Credit OAS**: tools/quant/data/newdata/BAML*.csv = **2023-09+ ONLY (793 rows) — cannot support a
  2008+ gate** (charter's BAML idea blocked by span). Long alternative used instead: FRED
  aaa/baa (Moody's, 1983+/1986+, n08 4649, clean) → baa-aaa spread mean 0.95%, range 0.40-3.50%.
  hy_oas in FRED dir = also 2023-08+ only (785 rows). T10YIE/T5YIE/DFII10: 2003-01+ daily, clean.
- **hyg/lqd as credit instruments**: real ETF prices as above; BAML OAS used ONLY as timing signal
  (2023+ rejected by span), baa-aaa used as the long-history OAS proxy signal — this is the NOT-paper-
  synth variant the charter asked for: PnL from HYG/LQD ETF returns, never from synthetic spread levels.

## 2. FAMILY 1 — SECTOR-BASKET relative momentum/reversion (charter idea 1)
- Screen s10 (216 configs): pairs {XLE,XLB,XLF,XLI}×{mom,rev}×lb{10..252} + sector-vs-GLD/TLT/QQQ/AGG.
  Best single pair: XLB-XLF **rev lb21 SR 0.633**; momentum variants ≤0.43 — **relative momentum is
  DEAD in this space, z-reversion is the only sign of life** (consistent with prior hunts: EM FX
  z-rev, CFX4).
- 6-pair basket (incl XLE pairs) z-rev grid (32 configs, s13): best gate1.5 lb10 SR 0.905 BUT 3 negy
  (worst -4.47%), and XLE pairs contribute the neg years: P5 basket (adds XLE-XLF, XLE-XLI) SR 0.115,
  11 negy — **the XLE relative is oil-dominated and destroys the book** (matches champion already
  owning Brent-WTI energy-relative exposure).
- **SEC3 = industrial trio** (XLB-XLF, XLB-XLI, XLF-XLI; XLE excluded on the oil-redundancy rationale):
  w = clip(-z15/1.5, ±0.5) per leg, EW across 3 books.
  **GATES 2008+ (n=4682)**: SR **0.667** PASS | ann_geo 3.66% | MDD -9.8% | H1 0.89 / H2 0.33 PASS |
  negy **8/19 (worst -3.60% 2016) FAIL** (2013 -2.02, 2015 -1.27, 2016 -3.60, 2017 -0.64, 2021 -2.26,
  2022 -2.80, 2023 -2.17, 2024 -1.55) | 10d-block position-lag scramble p=**0.000** (seeds 0/1/2,
  200x each) PASS | ac1 -0.052 PASS | uniqR 1.000 PASS | corr to champion **+0.016** (n=4665) PASS →
  **6/7**.
  Robustness: cap 2.0 → 0.628; lb21 → 0.633; lb(15,21) → 0.657; lb(21,63) → 0.564; hysteresis-exit →
  0.623; sign-flip → 0.421 (z-scaled sizing is the edge, not binary); T+2 0.667 / T+3 0.022 (fast-decay
  consistency check — NO same-day leak in file, shift verified); LOYO min **-1.055 (2016)** max +2.00
  (2008); OOS17+ **0.266**, OOS20+ 0.177, OOS23+ 0.242 — **edge concentrated 2008-2016; recent regime
  weak** (the honest reason this is a near-miss even ignoring the yearly gate); scrub5/10/20
  0.591/0.513/0.450. Costs: turnover 16.0%/day one-side → 2.43%/yr drag + 0.21%/yr borrow; gross
  exposure mean 0.82x max 1.00x. Marginal at champion: w=0.10 → SR_d 3.940→3.971, ann 41.5→39.2%,
  MDD -4.92→-4.7ish, 0 negy — same SR-lift/ann-cost shape as FXD1, does NOT close the ann≥80 gap.
  Dedup: unrelated to CFX4 (FX), a6r7 (bond trend), diescrack — data domain (SPDR sector ETFs) is new
  to the pool.

## 3. FAMILY 2 — RATES-CURVE 2s10s / 5s30s steepener (charter idea 2) — **DEAD**
- Paper-spread books (signal on DGS spread level, PnL = w·Δspread, frozen conv): 32 configs s16 +
  84 configs s11 (naive conv). Best anywhere: **2s5s sign lb21 SR 0.459** but H1 0.08 / H2 1.02
  (post-2013 only), MDD -24.6%, 7 negy; 2s10s ≤0.30 with 2008 -15.3%; 5s30s ≤0.23; 5s10s/10s30s/7s20s/
  1s10s ≤0.45 or negative. Momentum on spreads ≈ reversion on spreads ≈ nothing after 2015 (ZIRP+QE
  regime change); nothing within 0.15 of the 0.6 bar on H1/H2 simultaneously.
- **REAL-ETF DV01 books** (IEF 7.5y vs TLT 17y duration weights, 5s30/10s30 shape, and AGG hybrids):
  ALL NEGATIVE — best ieftlt rev126 SR 0.389 (negy 6), dv01-z variants -0.58..-1.25 SR with 15-17 neg
  years. Curve trades executed via ETFs have NEGATIVE expectancy on this data.
- **Distinctness vs existing rate sleeves (charter corr<0.15 check)**: champion corr of the 2s5s
  best-config = -0.002 (n=4667), i.e. family is decorrelated but has NO edge — decorrelation without
  alpha is worthless. C2_steep_carry corr to champion measured +0.046 (it stays the curve exposure).

## 4. FAMILY 3 — CREDIT-OAS momentum on REAL HYG/LQD (charter idea 3) — **DEAD**
- Ratio momentum/reversion on HYG/LQD (real ETFs): 36 configs, best **rev lb63 SR 0.227** (H2 0.00,
  7 negy) — nothing.
- baa-aaa OAS level/change as timing signal on HYG, HYG-LQD, HYG-IEF, HYG-TLT, LQD-TLT: 70 configs,
  best **HYG-IEF oas-mom lb63 SR 0.269** (9 negy, worst -12.4%) — fails everything. T10YIE-timed XLE
  (inflation-expectations → energy): best mom63 SR 0.379, MDD -72%, 6 negy.
- Conclusion: the credit cycle on ETF proxies is either already-priced in 6bps or dominated by equity
  beta; no 2008+ constructible OAS signal on disk produces SR≥0.6. **baa-aaa is a slow monthly-rev
  signal with ~4.6y of daily data — 2023+ BAML files — too short for any gate.**

## 5. ADDITIONAL DEAD ENDPOINTS (screened, not charted)
- GLD-vs-TLT/IEF (gold-rates relative) z-rev: SR -0.35..-0.19, 10-12 negy (2025 -22.8%); GLD-XLB: ≤0.01.
  The 2025 gold melt-up makes every short-gold/long-rates config blow up — no reversion edge.
- Momentum (non-rev) on every sector pair incl QQQ/SPY relatives: ≤0.43 — see §2.
- XLB-XLI single pair (cleanest data, no XLF): SR 0.239 — basket breadth is required.

## 6. SELF-AUDIT / BUGS CAUGHT THIS SESSION (methodology ledger)
1. **Scramble on net-of-cost returns instead of raw** (double-applying position): caught by sanity-
   checking my 10d-block implementation against FXD1 (known p=0.000) — my broken version printed
   p≈0.5 with "real SR -0.803" on a sleeve whose true SR is +0.87. ALL scramble p-values in this
   file are from the corrected raw-return implementation (T+1 inside pnl(), costs+borrow on rolled
   position only).
2. **Leg-level scramble pd.concat duplicate-column aliasing** (XLB appears in 2 books): pooled
   position matrix silently overwrote columns by name → garbage real SR (-7.39). Fixed with unique
   column names; verified pooled pnl == build pnl to 1e-12 before scrambling.
3. **Double-shift error** (passing already-shifted positions into a function that shifts again):
   produced same -7.39 figure; root-caused via day-level diff (2008-07-16 flagged) → fixed.
4. Earlier-session (partial-run) convention error also found: s1_dexgrid used net-of-EW-position
   ("pooled") accounting while FXD1 frozen convention is per-leg |Δw|/2 — SEC3 numbers quoted here
   use the FROZEN per-leg convention (the conservative one: higher measured cost, lower SR).

## 7. DEAD/BLOCKED LEDGER ADDITIONS (for DEAD_IDEAS.csv)
- rates-curve steepener mom/rev (DGS daily, all tenor pairs, 2008+): **dead** (best 0.459, no config
  passes halves; ETF-DV01 execution negative).
- credit-OAS momentum/reversion on real HYG/LQD with baa-aaa or T10YIE signals: **dead** (≤0.269).
- BAML OAS daily as 2008+ signal: **blocked** (data starts 2023-09, 793 rows).
- sector-pair RELATIVE MOMENTUM (all SPDR pairs on disk): **dead** (≤0.43); sector z-rev WITH XLE
  legs: **dead** (oil-redundant, SR 0.115 basket).
- gold-vs-rates relative z-rev: **dead** (negative, 2025 concentration risk).
- XLK/XLY/XLP/XLU/XLV sector relatives: **blocked** (no price files on disk).

## 8. WHAT WOULD CHANGE MY VERDICT
- Real XLK/XLU/XLV/XLY/XLP daily closes (9-sector SPDR set) → larger z-rev basket breadth might lift
  SR toward 1.0 and cut the neg-year count (6-book version was SR-degraded by XLE, not by breadth per se).
- A clean XLF price source pre-2010 (the twelvedata file's 2008 vol is 1.7x SPY's — suspect) could
  reprice SEC3's 2008-09 PnL either way.
- If the loop relaxes the yearly gate to ≤8 neg yrs with worst>-4% (dd-tolerant, as FXD1 suggested),
  SEC3 qualifies immediately (worst -3.60%) — but the OOS17+ SR 0.266 decay is the more fundamental
  problem and I would NOT blend it above w=0.05-0.10.

## 9. FILES
- sleeves/SEC3_sector_trio_zrev_daily.csv + .meta (NEAR-MISS deliverable, 6/7)
- campaign/scripts/sec3_sector_trio.py (frozen repro; rerun verified byte-identical, SR 0.6669)
- scratch/: lib.py, s10_sector.py(+s10_sector_results.csv 216 rows), s11_rates.py(+84 rows),
  s12_credit.py(+106 rows), s13_champ.py, s14_final.py, s15_gate.py, s16_sweep.py(+full sweep),
  s17_diag.py (cost/OOS/LOYO/scrub/marginal)

HUNT_CROSSASSET2 DONE
