# HUNT_INDUSTRY48 FINDINGS — Ken French 48-industry hunt (iter6, 2026-09-03)

**VERDICT: NEGATIVE. 0/2 engines delivered.** No KF48 industry engine passes the charter gates.
Charter instruction followed: "If nothing passes, log exact numbers + add dead families, do NOT
force a sleeve." No sleeves/*.csv emitted (nothing admissible). Repro: `scratch/repro_negatives.py`
(run ~2min, uses `scratch/lib48.py`). TDD battery: `scratch/tdd_gates.py` (all GREEN; stub
`stub_builder.py` still RED — Red-Green verified).

## 1. DATA PREMISE (fail-closed, verified fresh)
- File: tools/quant/data/kenfrench/48_Industry_Portfolios_Daily.csv, "Average Value Weighted
  Returns -- Daily" section: header line idx 9 (",Agric,Food,Soda,..."), 26,274 raw rows
  19260701→20260630, 48 columns, 49 fields/row verified.
- Missing codes: token scan of the VW section found EXACTLY one code: '-99.99' x 56,325 cells
  (all pre-1964); 0 missing cells in 2008+. Legit crash returns (e.g. -53.62, -45.65) preserved.
- After masking -99.99/-999 exactly and dropping non-live lead-in: panel 1969-07-01→2026-06-30,
  14,371 rows, 48 cols, 0 NaN in 2008+, worst legit daily return -30.65%.

## 2. TDD EVIDENCE (SUPERPOWERS: RED observed BEFORE GREEN)
| test | property | stub (RED) | lib48 (GREEN) |
|---|---|---|---|
| T1 leak | Δnet[t] from signal flip at t = 0; Δnet[t+1] > 0 | 4.792e-02 / 2.400e-03 FAIL | 0.000e+00 / 7.618e-03 PASS |
| T2 cost recon | max\|Σ gross − Σ\|ΔW\|·6.4e-4 − borrow − net\| < 1e-12; COST=6.4e-4; both sides pay | 1.282e-01 FAIL (stub charged 12bps, leak) | 0.000e+00 PASS |
| T3 scramble | poslag (roll POSITIONS) kills synthetic edge; return-roll control preserves it | perm SR median −2.717 FAIL (return-roll shipped) | p=0.000, med −2.883; control return-roll med +55.463 PASS |
| T4 data lint | 0 cells ≤ −0.99 in loaded panel | 56,325 FAIL (before fix) | 0 PASS |

## 3. BUG LEDGER (systematic-debugging: root cause before fix)
1. **T2 test double-shift** — my test re-shifted already-executed weights W (builder aligns
   `sig.shift(1)` internally). Evidence: recon err 1.762e-01 with double shift → 0 after fix.
   Test-side bug; builder correct.
2. **load48 dropped header names** (cols were ints 1..48) — name-based industry picks failed
   (KeyError Steel). Fix: parse cols from header line; assert len==48.
3. **First missing-code fix was WRONG** (`where(df>-0.99)` would delete legit crash returns).
   Caught by token-counting the raw CSV (one single code token '-99.99'). Correct fix: exact
   `np.isclose(-0.9999/-9.99/-999.0)` mask. RED→GREEN under new T4.
4. **ev() union-index inflation** — passing full-index sig + 2008-only R into vt_scale created
   ~20k zero-gross rows → expanding std collapsed → scale pinned at cap 3.0. Effect: ann/MDD
   inflated in one intermediate print (MDD -100%); SR UNAFFECTED (scale-invariant). Fixed by
   aligning sig to R08 before vt; final tables are clean (worst MDD -93.4%).
5. **Effective-lag mislabeling in 1d-reversal scan** — building the rank from R.shift(1) plus the
   builder's shift made an UNINTENDED lag-2 book. Honest decomposition (2008+, K12, 1/12 legs):
   lag-1 decision gross SR −0.152 (no edge); lag-2 gross SR +0.335 (stale-price reflection only).

## 4. CONVENTIONS (strict)
T+1 exec (decision t, executed W_t = sig_{t-1}); **6.4bps/side on Σ|ΔW| (both sides pay — per
TRADE_RECORD_STANDARD qty=|ΔW| per record)**; borrow 0.5%/yr on shorts; vt10 expanding min-60d
cap 3, first 60d scale=1.0; eval 2008-01-01+. NOTE: this cost convention is 2× the HUNT_FF2
lib (|ΔW|/2·6.4bps); negatives here are therefore CONSERVATIVE.

## 5. TRADE-RECORD / INSTRUMENT NOTE (mandatory disclosure)
All engines priced on the **KF48 industry VW portfolio return series** used as the tradable price
path → **price_source=SYNTH, instrument=KF48:<IndustryName>** (index-100 proxy standard) for ALL
48 legs. REAL sector-ETF coverage on disk is only XLF, SPY, QQQ (twelve_big) — i.e. 3/48
industries at best (XLF→Banks/Insur/Fin). **Real-ETF execution fidelity is UNVERIFIED for ≥45/48
industries**; even a gate-passing signal would have carried this disclosure. No blotter emitted
(no delivered engine). Portfolio-level VW returns are NOT directly tradeable at 6.4bps for
high-turnover books (see F5).

## 6. GATE CARDS (exact numbers; gates: SR≥0.6 | H1,H2≥0.3 | ≤2 neg yrs each >−5% | poslag p<0.05
| ac1<0.5 | uniqR≥0.08 | \|corr\|<0.15 to V3 champion AND dualmom)

### Idea 1 — cross-industry relative momentum (EW K/K, T+1, vt10): DEAD (15 variants, all fail)
- mom lb21 K3/K6/K12: SR −0.610/−0.574/−0.653; lb63: −0.196/−0.158/−0.275; lb126: −0.049/−0.044/−0.092
- 12-1 (252−21 skip) K3/K6/K12: SR −0.555/−0.788/−0.836
- sharpe63 K6: SR −0.227; longonly 12-1 K12 (BEST of family): gate card below
- **BEST (longonly 12-1 K12): SR 0.2175 FAIL(gate 0.6) | H1 −0.0503 H2 0.4782 FAIL | negy 6/19
  worst −23.93% (2008) FAIL | poslag p=0.7000 FAIL (med perm SR +0.259 vs real +0.212 → the +0.22
  is indistinguishable from noise) | ac1 −0.0596 pass | uniqR 0.9998 pass | corr V3 +0.0877 pass,
  corr dualmom +0.5393 FAIL** → 3/7 gates. Not deliverable.
- turnover 30–106×/yr → costs ≤68bp/yr; failure is NOT cost-driven: gross momentum among 48
  industries is ≈0 (L/S) post-2008.

### Idea 2 — momentum-acceleration CARDS (mom63 − mom63.shift(20)): DEAD
- accel K6: SR −1.055, ann −9.87%, H1 −1.18 H2 −0.96 (K3/K12 in first pass: −0.992/−1.098)

### Idea 3 — leader/breadth timing of laggards: DEAD (all 5 variants)
- lagRev12 × breadth>0.4: SR −1.443 (turn 208/yr); × lead21z<0: −0.558; × disp z: dead (both
  regimes); mom12 × breadth>0.4: −1.519. Laggard reversal in the 48 is itself negative
  (unconditional lb63 K12 flip: −0.275→ reversal long-laggards also ≤0) — gates add no edge.

### Idea 4 — industry "carry"/idle-column proxies: DEAD (7 variants)
- def-vs-cyc ratio63 L/S: SR +0.170, H1 −0.37 FAIL (regime-flipped); pairs z63 RlEst-Util −0.011,
  Banks-Insur −0.003, Telcm-Comps −0.398, Meals-Rtail +0.017 (first pass); mom126 top3 vol-filtered
  L-only +0.200 (turn 28×/yr cost-dead, H1 +0.04).

### Idea 5 — 1-day industry reversal/continuation: DEAD BY COSTS (microstructure artifact)
- lag-1 decision (correct T+1): gross SR −0.152 → NO edge at tradable lag.
- lag-2 stale variant: gross SR +0.3358, |gross| 62.3bp/day vs cost 18.6bp/day (**cost/gross
  1.617**); NET SR −2.9824 daily; weekly-hold NET −0.820; lag-3/5 gross +0.181/+0.273.
- Interpretation: half-life <2 days; the "edge" needs the T−1→T+1 skip (stale/reflection), dies
  under any realistic execution frequency × cost. Consistent with HUNT_EQMOM domain boundary.

## 7. CORR CHECKS (family-level)
All engines |corr| ≤ 0.15 to GOAL100_HONEST14V3_BALANCED (range −0.056..+0.088) — decorrelated
BUT useless (no alpha). Best candidate is corr +0.5393 to dualmom — NOT decorrelated from the
existing equity-L/S sleeve, so even its noise-level SR wouldn't blend.

## 8. DEAD FAMILIES TO APPEND TO DEAD_IDEAS.csv (coordinator merge; agent wrote only own dir)
```
KF48 cross-industry rel momentum L/S (lb21/63/126, 12-1, sharpe63; K3/6/12),dead,15 variants SR -0.92..-0.04 net 2008+ (gross~0, not cost-driven),HUNT_INDUSTRY48
KF48 12-1 long-only top-12,dead,SR 0.2175 poslag p 0.700 corr dualmom +0.539 (noise+redundant),HUNT_INDUSTRY48
KF48 mom-accel CARDS,dead,SR -1.055,HUNT_INDUSTRY48
KF48 leader/breadth-gated laggard books,dead,SR -1.52..-0.46 5 variants,HUNT_INDUSTRY48
KF48 def-vs-cyc ratio + 4 industry pairs,dead,SR -0.40..+0.17 no H1/H2 consistency,HUNT_INDUSTRY48
KF48 1d industry reversal,dead,"gross +0.336 only at stale lag-2, cost/gross 1.62, net -2.98 daily -0.82 weekly",HUNT_INDUSTRY48
```

## 9. VERIFICATION-BEFORE-COMPLETION
Every number above is from fresh runs in this session (stdout quoted verbatim in scratch logs;
key runs reproducible via `python3 scratch/tdd_gates.py lib48` → exit 0, and
`python3 scratch/repro_negatives.py`). No "should/probably" claims. Negative result is itself
TDD-backed: the engine battery passed all four reconciliation tests before any strategy number
was accepted into evidence.
