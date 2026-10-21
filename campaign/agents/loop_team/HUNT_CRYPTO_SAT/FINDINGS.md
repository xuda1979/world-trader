# HUNT_CRYPTO_SAT FINDINGS (iter 7.5, 2026-09-03) — crypto satellite, TDD, campaign/bt

VERDICT: **NEGATIVE / DISCLOSED-NEAR-MISS SATELLITE — delivered as sleeve, NOT champion-eligible.**
A long-only BTC/ETH-major crypto TSMOM satellite is REAL, decorrelated (corr 0.05), and its own-span
SR clears 1.0, but it FAILS the annual gates on its actual span (4 negative years of 10) and the
position-lag scramble needed a cost-recharging re-run to clear (p 0.039, marginal). Per charter step 3
"else log exact numbers as negative": logged below with every exact number.

## 0. TDD (SUPERPOWERS_RIGOR) — RED observed before GREEN
- RED: tests/test_crypto_longonly.py written FIRST; ran: `ModuleNotFoundError: crypto_lib` (2 failed,
  5 framework-property tests), plus a negative-control test proving the long-only clamp test has
  teeth (L/S builder generates negative weights; control passes => the test would catch it).
- GREEN after minimal crypto_lib: 8/8 pass. Framework regression: campaign/bt/tests 28/28 pass.
- Final suite: **36 passed in 0.11s** (8 crypto + 28 bt).
- Two REAL emitter bugs found+fixed by these tests (systematic-debugging, root causes documented):
  1. Ledger emitted from a SLICED weight path (trade-days only) => pandas .diff() skipped no-trade
     gaps, understating turnover 2.3% rel (e.g. BTC ledger 6.6428 vs true path 6.6761). Fix: emit
     from the FULL weight path; final reconcile max_rel 2.418e-16.
  2. make_mark_ledger had a shadowed-variable bug (`px` reused inside its own comprehension) and a
     missing px param — caught as NameError/ValueError by the P6 tests; fixed and re-proven.
  3. Probe-only (not a framework bug): groupby(...).apply(lambda (1+x).prod()-1) pandas warmup-call
     trap produced absurd yearly compounds; replaced with direct groupby prod (numbers re-verified).

## 1. DATA PREMISE (lint, fail-closed confirmed)
- 12 coins, more_crypto/*.csv, REAL prints (Binance Vision primary + twelvedata tail): BTC 3305 rows
  2017-08-17..2026-09-03, ETH 3168, BNB 3224, LTC 3187, ADA 3062, XRP 3045, LINK 2652, SOL 2215
  (2020-08-11+), DOGE 2378, DOT 2208, AVAX 2103, MATIC 2213 (one 14d gap 2024-08-31..09-13).
- No zero/negative closes, no NaN closes, no dup dates (spot-checked all four; |r|>0.5 extremes:
  BTC/ETH/SOL 0, MATIC 2). Ann vol: BTC 67%, ETH 85%, SOL 115%, MATIC 118%.

## 2. SINGLE-NAME SWEEP (72 variants = {tsmom 21/63/126, rev 1/3/5} x 12 coins; long-only,
vt10/expanding-60/cap3, weight cap 1.0, 6.4bps/side, T+1, on-span after 90d warmup; CSV scratch/)
- BEST: SOL tsmom126 SR **1.302** (H1 1.553 H2 0.995, corr 0.059) — but **scramble p=0.130 FAIL**;
  n=2125, 2 neg yrs. RUNNER: SOL tsmom63 SR 1.221 p=0.110 FAIL. Selection risk acknowledged.
- BTC deepest history (n=3215): tsmom21 SR 0.860 (H2 0.481, 3 neg yrs); tsmom252 win120 tgt20% SR 0.714.
- REVERSAL family DEAD long-only: best LINK rev1 SR 0.773 (H2 0.353, p 0.065); 40+ of 60 variants
  SR<0.30; crypto trends rather than reverts at daily scale => reversals structurally weak here.
- L/S-PAPER (shorts NOT tradeable at retail — disclosed, not deliverable): panel tsmom21 LO 1.125 vs
  L/S 0.713; panel rev3 LO 0.152 vs L/S −0.759; rev5 L/S −0.644. Shorts REDUCE SR => long-only is
  both the honest and the better construction.

## 3. PANEL BOOK (champion-candidate): CRYPTO_TSMOM21LO — DELIVERED (as near-miss sleeve)
Budget 1.0 split 1/n_avail across listed coins, long-only, vt10/60/cap3, T+1, 6.4bps/side,
capital-real gross mean 0.0969 max 0.2453. Span 2017-11-15..2026-08-27, n=3215 (7d/wk calendar).
- **SR_d 1.109** (H1 1.701 / H2 0.210), SR_m 0.930, ann_geo +9.48%, ann_arith +9.42%, MDD −16.61%,
  **neg 4/10** (2018 −6.85%, 2022 −12.44%, 2025 −0.96%, 2026 −2.22%), ac1 +0.032, uniq 0.807,
  top-50d |PnL| share 12.9% (no concentration flag).
- **Corr to HONEST14V3_BALANCED +0.0535; corr to RAW-EW13@1.6x +0.0403 — charter |corr|<0.10 PASSES.**
- Sub-period SR: 2017-18 +0.847, 2019-20 +1.595, 2021-22 +1.508, 2023-24 +1.078, **2025-26 −0.226**
  (edge currently dormant; 2026 YTD −2.2%).
- Scramble: bt.gates.scramble_positions (uncosted, correct real-book baseline): p 0.083–0.130 across
  variants = **FAIL at 0.05**. With 6.4bps re-charged on scrambled turnover (harsher/correct):
  p = 0.0385 (seed7) / 0.0410 (seed11) / 0.0400 (seed13), n=2000 => marginal PASS; negative control
  (positions rolled +500: SR 0.463 vs real 0.905) gives p=0.726 — the test has teeth; the book just
  does not clear the framework's own gate. Recorded as FAIL (conservative).

## 4. 2008+ SPAN HONESTY (charter predicted: satellite CANNOT satisfy 2008+ gates — CONFIRMED)
Padded onto champion calendar (weekend PnL compounded into next NYSE day; 0 before listing):
- tsmom21 padded 2008+: SR 0.908, H1 0.000 (pre-listing zero-run 2416d), **neg 4/19**, worst −12.44%,
  MDD −16.61%, corr +0.038, zruns>=20d [2416, 23]. FAILS neg-yr and halves gates, exactly as the
  charter anticipated. tsmom63/126 and rev1 padded: same structure (neg 4/19, H1 0.000).

## 5. BLEND INTO RAW-EW13@1.6x (charter step 3; window-exact; both streams net of own costs)
Combined gross = (1−w)*1.6 + w*1.0 ≤ 1.6 always (satellite long-only, gross 0.10) — leverage SAFE.
- w=0.05: SR 4.038→**4.079** (dSR +0.041), MDD −3.40%→−3.26%, ann 31.19%→29.95%, neg 0→0/10.
- w=0.10: SR 4.038→**4.100** (dSR +0.063), MDD −3.40%→−3.12%, ann 31.19%→28.73%, neg 0→0/10,
  worst blended yr +3.91% (2018/2022 crypto winters absorbed by the 0.9 RAW offset).
- w=0.20: dSR +0.023; from 2020-11 start: w=0.10 dSR +0.028, w=0.20 dSR −0.081.
- SPLIT: 2017-2024 control 4.105→4.191, but 2025-2026 control 3.748→**3.692 (detrimental today)**.
- Verdict: max lift dSR +0.063 at w≤0.10 — far below the campaign materiality bar that already
  killed the vol/timing overlays at dSR +0.035..0.15. SAME VERDICT: not deliverable as alpha.

## 6. GATE CARD (delivered CRYPTO_TSMOM21LO, exact numbers)
| gate | value | threshold | verdict |
|---|---|---|---|
| SR_d own span n=3215 | 1.109 | ≥0.6 | PASS |
| H1 / H2 | 1.701 / 0.210 | both ≥0.3 | **FAIL** (H2) |
| neg years own span | 4/10 (worst −12.44%) | ≤2 | **FAIL** |
| neg years padded 2008+ | 4/19 | 0 | **FAIL** |
| MDD | −16.61% | info | — |
| corr vs V3_BAL / RAW-EW13 | +0.0535 / +0.0403 | |corr|<0.10 | **PASS** |
| ac1 / uniqR | +0.032 / 0.807 | <0.5 / ≥0.08 | PASS |
| scramble (bt.gates) | p 0.083–0.130 | <0.05 | **FAIL** |
| scramble (cost-recharged) | p 0.0385–0.0410 | <0.05 | marginal PASS |
| ledger PnL repro | max\|diff\| 6.939e-18 | <1e-10 | PASS |
| turnover reconcile | ok=True, max_rel 2.418e-16 | <1e-8 | PASS |
| T+1 / long-only / 6.4bps / borrow 0 | enforced via bt.engine + TDD tests | — | PASS |

## 7. TRADE-RECORD (TRADE_RECORD_STANDARD compliance)
instrument: {BTC,ETH,BNB,LTC,ADA,XRP,LINK,SOL,DOGE,DOT,AVAX,MATIC}-USDT spot; price_path:
tools/quant/data/more_crypto/{SYM}.csv close; **price_source REAL** (3549/3549 trade rows carry
non-NaN REAL prices); sides {BUY,SELL}; cost_bps 6.4 uniform; 3549 trade rows + 38,580 mark rows
(ledger_full). Byte-repro: two independent builds sha256-identical (a88803bd48071b28).
Files: sleeves/CRYPTO_TSMOM21LO_{net,weights,ledger,ledger_full}.csv + CRYPTO_TSMOM21LO.meta.json.
Repro: crypto_lib.py, panel_build.py, test_crypto_longonly.py (+red control) in this agent dir.

## 8. WHY NOT DELIVERED AS A CHAMPION SLEEVE (brutally honest)
1. Fails annual gates on its own span (4/10 neg yrs, H2 0.210) and cannot satisfy 2008+ gates.
2. Fails the framework's own position-lag scramble; only a harsher costed variant passes marginally.
3. Blend lift (dSR +0.063 max at w=0.10) is below every materiality bar this campaign has applied.
4. 2025-26 SR −0.226: the 2019-2022 carry was crypto adoption drift, not a durable tradeable premise.
All exact numbers above are from fresh in-session runs via campaign/bt on the delivered files.
